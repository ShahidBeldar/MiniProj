"""
news_fetcher.py — Free RSS feed parser, no API key needed.
Falls back to curated sample news if feeds are unavailable.
"""

import feedparser
import streamlit as st
import pandas as pd
from datetime import datetime
import re


# ── RSS FEED SOURCES ──────────────────────────────────────────────────────────
RSS_FEEDS = {
    "Reuters Business":      "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Technology":    "https://feeds.reuters.com/reuters/technologyNews",
    "ET Markets":            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol":          "https://www.moneycontrol.com/rss/marketreports.xml",
    "Seeking Alpha":         "https://seekingalpha.com/feed.xml",
    "Yahoo Finance":         "https://finance.yahoo.com/news/rssindex",
    "Bloomberg Markets":     "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC Business":         "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "Economic Times India":  "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "Livemint":              "https://www.livemint.com/rss/markets",
}

# Tickers to scan for in headlines
TICKER_KEYWORDS = {
    "TSLA":      ["tesla", "elon musk", "cybertruck", "model 3", "model y", "giga"],
    "AAPL":      ["apple", "iphone", "tim cook", "ios", "mac", "app store", "vision pro"],
    "GOOGL":     ["google", "alphabet", "youtube", "waymo", "deepmind", "bard", "gemini"],
    "MSFT":      ["microsoft", "azure", "satya nadella", "windows", "copilot", "activision", "github"],
    "NVDA":      ["nvidia", "jensen huang", "h100", "cuda", "blackwell", "geforce"],
    "AMZN":      ["amazon", "aws", "andy jassy", "prime", "alexa", "whole foods"],
    "RELIANCE":  ["reliance", "mukesh ambani", "jio", "ril", "ajio"],
    "TCS":       ["tcs", "tata consultancy", "n chandrasekaran", "tata group"],
    "INFY":      ["infosys", "salil parekh", "narayana murthy"],
    "WIPRO":     ["wipro", "thierry delaporte", "srinivas pallia"],
    "HDFCBANK":  ["hdfc bank", "hdfc", "sashidhar jagdishan"],
}

# Sentiment keywords
POSITIVE_WORDS = ["record", "beats", "surge", "rally", "growth", "profit", "revenue",
                  "milestone", "deal", "upgraded", "strong", "win", "launch", "breakthrough",
                  "rises", "gains", "expands", "acquires", "partnership", "bullish"]
NEGATIVE_WORDS = ["fine", "fined", "recall", "investigation", "probe", "lawsuit", "decline",
                  "miss", "cuts", "layoffs", "resignation", "fraud", "ban", "restrict",
                  "loss", "falls", "drops", "disappoints", "warning", "risk", "default"]


def quick_sentiment(text: str) -> tuple[str, float]:
    """
    Quick keyword-based sentiment for RSS items.
    Returns (label, polarity).
    """
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg + 1:
        return "POSITIVE", round(0.4 + min(pos * 0.05, 0.4), 2)
    if neg > pos + 1:
        return "NEGATIVE", round(-0.4 - min(neg * 0.05, 0.4), 2)
    return "NEUTRAL", 0.0


def detect_tickers(headline: str) -> list[str]:
    """Detect which tickers are mentioned in a headline."""
    h = headline.lower()
    found = []
    for ticker, keywords in TICKER_KEYWORDS.items():
        if any(kw in h for kw in keywords):
            found.append(ticker)
    return found or ["GENERAL"]


def is_rumour(headline: str) -> bool:
    rumour_signals = ["sources say", "reportedly", "according to insiders",
                      "unconfirmed", "rumour", "rumor", "could", "might consider",
                      "is said to", "people familiar"]
    h = headline.lower()
    return any(sig in h for sig in rumour_signals)


@st.cache_data(ttl=600)   # 10-minute cache
def fetch_rss_news(max_items: int = 40) -> pd.DataFrame:
    """
    Fetch and parse RSS feeds. Returns DataFrame with columns:
    source, title, published, link, tickers, sentiment, polarity, is_rumour
    """
    items = []

    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if not title or len(title) < 15:
                    continue

                # Parse date
                published = entry.get("published", "")
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6])
                        pub_str = dt.strftime("%d %b, %H:%M")
                    else:
                        pub_str = "Recent"
                except Exception:
                    pub_str = "Recent"

                label, polarity = quick_sentiment(title)
                tickers = detect_tickers(title)

                items.append({
                    "source":    source_name,
                    "title":     title,
                    "published": pub_str,
                    "link":      entry.get("link", ""),
                    "tickers":   ", ".join(tickers),
                    "sentiment": label,
                    "polarity":  polarity,
                    "is_rumour": is_rumour(title),
                })
        except Exception:
            continue  # Skip broken feeds silently

    if not items:
        return _fallback_news()

    df = pd.DataFrame(items).drop_duplicates(subset="title")
    return df.head(max_items).reset_index(drop=True)


def _fallback_news() -> pd.DataFrame:
    """Return curated sample news when RSS is unavailable."""
    fallback = [
        {"source":"Reuters","title":"Tesla faces record $4.2B EU fine over autopilot safety violations","published":"Today","link":"","tickers":"TSLA","sentiment":"STRONG_NEGATIVE","polarity":-0.82,"is_rumour":False},
        {"source":"Bloomberg","title":"Reliance Jio surpasses 500M subscribers ahead of analyst expectations","published":"Today","link":"","tickers":"RELIANCE","sentiment":"STRONG_POSITIVE","polarity":0.79,"is_rumour":False},
        {"source":"CNBC","title":"Apple Vision Pro 2 launch confirmed for Q3, supply chain partners rally","published":"Today","link":"","tickers":"AAPL","sentiment":"POSITIVE","polarity":0.61,"is_rumour":False},
        {"source":"ET Markets","title":"RBI holds rates steady, signals cautious easing in H2","published":"Today","link":"","tickers":"NIFTY","sentiment":"NEUTRAL","polarity":0.05,"is_rumour":False},
        {"source":"Mint","title":"TCS Q2 guidance disappoints, management warns of client budget freeze","published":"Today","link":"","tickers":"TCS","sentiment":"NEGATIVE","polarity":-0.63,"is_rumour":False},
        {"source":"WSJ","title":"NVIDIA announces Blackwell Ultra GPU with record AI performance","published":"Today","link":"","tickers":"NVDA","sentiment":"STRONG_POSITIVE","polarity":0.85,"is_rumour":False},
        {"source":"Reuters","title":"Infosys wins $1.8B deal with European bank for core modernisation","published":"Today","link":"","tickers":"INFY","sentiment":"POSITIVE","polarity":0.67,"is_rumour":False},
        {"source":"Bloomberg","title":"Sources say Amazon in early talks to acquire logistics startup for $3B","published":"Today","link":"","tickers":"AMZN","sentiment":"POSITIVE","polarity":0.44,"is_rumour":True},
        {"source":"CNBC","title":"Microsoft Azure revenue grows 28% as AI workloads accelerate","published":"Today","link":"","tickers":"MSFT","sentiment":"POSITIVE","polarity":0.71,"is_rumour":False},
        {"source":"ET Markets","title":"HDFC Bank NIM pressure continues amid high cost of funds post-merger","published":"Today","link":"","tickers":"HDFCBANK","sentiment":"NEGATIVE","polarity":-0.48,"is_rumour":False},
    ]
    return pd.DataFrame(fallback)


def sentiment_dot_color(polarity: float) -> str:
    """Return color for sentiment indicator dot."""
    if polarity >= 0.4:   return "#00E8A0"
    if polarity >= 0.1:   return "#88CC88"
    if polarity >= -0.1:  return "#FFD060"
    if polarity >= -0.4:  return "#FF7D35"
    return "#FF3D60"
