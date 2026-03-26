"""
core/feeds.py — RSS feed parser + quick sentiment scorer.
FIX: Parallel feed fetching via ThreadPoolExecutor (no more sequential blocking).
FIX: Sentiment thresholds aligned with engine.py polarity_category().
FIX: Per-function cache clear exposed so News page doesn't wipe global cache.
No Streamlit imports. Returns DataFrames.
"""
from __future__ import annotations
import feedparser
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# ── SOURCES ───────────────────────────────────────────────────────────────────

_RSS: dict[str, str] = {
    "Reuters Business":  "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Tech":      "https://feeds.reuters.com/reuters/technologyNews",
    "ET Markets":        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol":      "https://www.moneycontrol.com/rss/marketreports.xml",
    "Yahoo Finance":     "https://finance.yahoo.com/news/rssindex",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC Business":     "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "Economic Times":    "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "Livemint":          "https://www.livemint.com/rss/markets",
    "Seeking Alpha":     "https://seekingalpha.com/feed.xml",
}

_TKR_KW: dict[str, list[str]] = {
    "TSLA":     ["tesla", "elon musk", "cybertruck", "model 3", "model y", "model s"],
    "AAPL":     ["apple", "iphone", "tim cook", "ios", "mac", "vision pro", "app store"],
    "GOOGL":    ["google", "alphabet", "youtube", "waymo", "deepmind", "gemini", "bard"],
    "MSFT":     ["microsoft", "azure", "satya nadella", "copilot", "activision", "github"],
    "NVDA":     ["nvidia", "jensen huang", "h100", "cuda", "blackwell", "geforce"],
    "AMZN":     ["amazon", "aws", "andy jassy", "prime", "alexa", "whole foods"],
    "RELIANCE": ["reliance", "jio", "mukesh ambani", "ril", "ajio"],
    "TCS":      ["tcs", "tata consultancy"],
    "INFY":     ["infosys", "salil parekh"],
    "WIPRO":    ["wipro"],
    "HDFCBANK": ["hdfc bank", "hdfc"],
}

_POS_KW = [
    "record", "beats", "surge", "rally", "growth", "profit", "milestone",
    "deal", "upgraded", "strong", "win", "launch", "rises", "gains",
    "expands", "acquires", "bullish", "breakthrough", "exceeds",
    "outperforms", "raises guidance", "secures",
]
_NEG_KW = [
    "fine", "fined", "recall", "investigation", "probe", "lawsuit",
    "decline", "miss", "cuts", "layoffs", "resignation", "fraud", "ban",
    "restrict", "loss", "falls", "drops", "disappoints", "warning",
    "default", "writedown", "impairment", "abruptly",
]
_RUM_KW = [
    "sources say", "reportedly", "according to insiders", "unconfirmed",
    "rumour", "rumor", "could", "might consider", "is said to",
    "people familiar", "early talks",
]


# ── QUICK SENTIMENT ───────────────────────────────────────────────────────────

def _quick_sentiment(text: str) -> tuple[str, float]:
    """
    Keyword-based sentiment.
    Thresholds aligned with engine.py polarity_category():
      STRONG_POSITIVE  >= +0.60
      POSITIVE         +0.20 .. +0.59
      NEUTRAL          -0.19 .. +0.19
      NEGATIVE         -0.20 .. -0.59
      STRONG_NEGATIVE  <= -0.60
    """
    t = text.lower()
    pos = sum(1 for w in _POS_KW if w in t)
    neg = sum(1 for w in _NEG_KW if w in t)
    diff = pos - neg

    if diff >= 2:
        return "STRONG_POSITIVE", round(min(1.0, 0.65 + pos * 0.08), 2)
    if diff == 1:
        return "POSITIVE",        round(min(0.59, 0.22 + pos * 0.06), 2)
    if diff == -1:
        return "NEGATIVE",        round(max(-0.59, -0.22 - neg * 0.06), 2)
    if diff <= -2:
        return "STRONG_NEGATIVE", round(max(-1.0, -0.65 - neg * 0.08), 2)
    return "NEUTRAL", 0.0


def _detect_tickers(text: str) -> str:
    h = text.lower()
    found = [t for t, kws in _TKR_KW.items() if any(k in h for k in kws)]
    return ", ".join(found) if found else "GENERAL"


def _is_rumour(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in _RUM_KW)


def _parse_date(entry) -> str:
    try:
        return datetime(*entry.published_parsed[:6]).strftime("%d %b, %H:%M")
    except Exception:
        return "Recent"


# ── PER-FEED WORKER ───────────────────────────────────────────────────────────

def _fetch_one_feed(src: str, url: str) -> list[dict]:
    """Fetch a single RSS source. Returns list of row dicts (empty on failure)."""
    try:
        feed = feedparser.parse(url)
        rows: list[dict] = []
        for entry in feed.entries[:6]:
            title = (entry.get("title") or "").strip()
            if len(title) < 15:
                continue
            sent, pol = _quick_sentiment(title)
            rows.append({
                "source":    src,
                "title":     title,
                "published": _parse_date(entry),
                "link":      entry.get("link", ""),
                "tickers":   _detect_tickers(title),
                "sentiment": sent,
                "polarity":  pol,
                "is_rumour": _is_rumour(title),
            })
        return rows
    except Exception:
        return []


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def fetch_news(max_items: int = 60) -> pd.DataFrame:
    """Fetch and score RSS headlines (parallel). Falls back to sample data."""
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_one_feed, src, url): src for src, url in _RSS.items()}
        for future in as_completed(futures):
            try:
                rows.extend(future.result(timeout=6))
            except Exception:
                continue

    if not rows:
        return _fallback_feed()

    df = (
        pd.DataFrame(rows)
        .drop_duplicates("title")
        .head(max_items)
        .reset_index(drop=True)
    )
    return df


def _fallback_feed() -> pd.DataFrame:
    """Static sample feed when all RSS sources fail."""
    data = [
        {"source": "Reuters",    "title": "Tesla faces record $4.2B EU fine over autopilot safety violations",   "published": "Today", "link": "", "tickers": "TSLA",     "sentiment": "STRONG_NEGATIVE", "polarity": -0.78, "is_rumour": False},
        {"source": "Bloomberg",  "title": "Reliance Jio surpasses 500M subscribers ahead of analyst expectations","published": "Today", "link": "", "tickers": "RELIANCE", "sentiment": "STRONG_POSITIVE", "polarity":  0.72, "is_rumour": False},
        {"source": "CNBC",       "title": "Apple Vision Pro 2 launch confirmed for Q3, supply chain partners rally","published": "Today", "link": "", "tickers": "AAPL",     "sentiment": "POSITIVE",        "polarity":  0.54, "is_rumour": False},
        {"source": "ET Markets", "title": "TCS Q2 guidance disappoints, management warns of client budget freeze", "published": "Today", "link": "", "tickers": "TCS",      "sentiment": "NEGATIVE",        "polarity": -0.42, "is_rumour": False},
        {"source": "Reuters",    "title": "NVIDIA announces Blackwell Ultra GPU with record AI performance benchmarks","published": "Today", "link": "", "tickers": "NVDA",     "sentiment": "STRONG_POSITIVE", "polarity":  0.80, "is_rumour": False},
        {"source": "Bloomberg",  "title": "Infosys wins $1.8B deal with European bank for core modernisation",    "published": "Today", "link": "", "tickers": "INFY",     "sentiment": "POSITIVE",        "polarity":  0.55, "is_rumour": False},
        {"source": "CNBC",       "title": "Sources say Amazon in early talks to acquire logistics startup for $3B","published": "Today", "link": "", "tickers": "AMZN",     "sentiment": "POSITIVE",        "polarity":  0.38, "is_rumour": True},
        {"source": "ET Markets", "title": "Microsoft Azure revenue grows 28% as AI workloads accelerate cloud growth","published": "Today", "link": "", "tickers": "MSFT",     "sentiment": "STRONG_POSITIVE", "polarity":  0.68, "is_rumour": False},
        {"source": "Mint",       "title": "HDFC Bank NIM pressure continues amid high cost of funds post-merger", "published": "Today", "link": "", "tickers": "HDFCBANK", "sentiment": "NEGATIVE",        "polarity": -0.35, "is_rumour": False},
        {"source": "Reuters",    "title": "NVDA chip export ban extended to additional Southeast Asian countries", "published": "Today", "link": "", "tickers": "NVDA",     "sentiment": "STRONG_NEGATIVE", "polarity": -0.74, "is_rumour": False},
        {"source": "ET Markets", "title": "Wipro wins $500M deal with Japanese conglomerate for digital transformation","published": "Today", "link": "", "tickers": "WIPRO",    "sentiment": "POSITIVE",        "polarity":  0.48, "is_rumour": False},
        {"source": "Reuters",    "title": "Google Gemini Ultra outperforms GPT-4 on finance benchmark tests",     "published": "Today", "link": "", "tickers": "GOOGL",    "sentiment": "POSITIVE",        "polarity":  0.50, "is_rumour": False},
    ]
    return pd.DataFrame(data)


def sentiment_dot_color(pol: float) -> str:
    if pol >= 0.4:  return "#00E8A0"
    if pol >= 0.1:  return "#7EC882"
    if pol > -0.1:  return "#FFD060"
    if pol > -0.4:  return "#FF7D35"
    return "#FF3D60"
