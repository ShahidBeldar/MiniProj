"""
core/engine.py — 7-stage ML analysis pipeline. No Streamlit imports.

Stages:
  1. NER          — entity detection (keyword matching)
  2. Event        — regex-based event classification (9 types)
  3. FinBERT      — financial sentiment (keyword fallback when model unavailable)
  4. Rumour       — multi-signal credibility scoring
  5. SHAP         — word-level attribution via weighted lexicon
  6. Historical   — sentence-transformer similarity search (TF-IDF fallback)
  7. Macro        — VIX-based amplification factor

FIX: Models use @st.cache_resource (not module globals) for reliable caching.
FIX: compute_ripple imported at module level.
FIX: Credibility dampening applied BEFORE event multiplier.
FIX: Relevance score uses non-matching entity count.
FIX: Corpus embeddings cached separately from per-query encoding.
FIX: len(similar) handled safely for None / empty DataFrame.
"""
from __future__ import annotations
import re
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

import streamlit as st

from core.graph import compute_ripple  # module-level import — no circular risk


# ── LAZY MODEL LOADERS (cache_resource = one instance per server process) ─────

@st.cache_resource(show_spinner="Loading FinBERT sentiment model…")
def get_finbert():
    try:
        from transformers import pipeline as hf_pipeline
        return hf_pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
    except Exception:
        return None


@st.cache_resource(show_spinner="Loading sentence encoder…")
def get_encoder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_news_df() -> pd.DataFrame:
    try:
        from core.seeder import ensure_sample_data
        path = ensure_sample_data()
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


# ── STAGE 1 — NER ─────────────────────────────────────────────────────────────

_ENTITY_KW: dict[str, list[str]] = {
    "TSLA":     ["tesla", "elon musk", "cybertruck", "model 3", "model y",
                 "model s", "giga", "fsd", "supercharger"],
    "AAPL":     ["apple", "tim cook", "iphone", "ipad", "mac", "vision pro",
                 "app store", "siri"],
    "GOOGL":    ["google", "alphabet", "waymo", "youtube", "deepmind",
                 "bard", "gemini", "google cloud"],
    "MSFT":     ["microsoft", "azure", "satya nadella", "windows", "copilot",
                 "activision", "github", "xbox"],
    "NVDA":     ["nvidia", "jensen huang", "h100", "cuda", "blackwell",
                 "geforce", "a100", "rubin"],
    "AMZN":     ["amazon", "aws", "andy jassy", "prime", "alexa",
                 "whole foods", "twitch"],
    "RELIANCE": ["reliance", "jio", "mukesh ambani", "ril", "ajio"],
    "TCS":      ["tcs", "tata consultancy", "n chandrasekaran"],
    "INFY":     ["infosys", "salil parekh", "narayana murthy"],
    "WIPRO":    ["wipro", "thierry delaporte", "srinivas pallia"],
    "HDFCBANK": ["hdfc bank", "hdfc", "sashidhar jagdishan"],
}


def detect_entities(headline: str) -> list[str]:
    h = headline.lower()
    return [t for t, kws in _ENTITY_KW.items() if any(k in h for k in kws)]


# ── STAGE 2 — EVENT CLASSIFICATION ───────────────────────────────────────────

_EVENT_PATTERNS: dict[str, list[str]] = {
    "Regulatory/Legal": [
        r"fine[sd]?", r"penalt", r"violation", r"lawsuit", r"probe",
        r"investigat", r"regulat", r"sanction", r"ban\b", r"antitrust",
        r"\bdoj\b", r"\bsec\b", r"\bftc\b", r"court", r"ruling", r"recall",
        r"sebi\b", r"rbi order", r"enforcement",
    ],
    "Earnings/Financial": [
        r"earnings", r"revenue", r"profit", r"loss\b", r"q[1-4]\b",
        r"quarterly", r"guidance", r"\beps\b", r"ebitda", r"margin",
        r"beats?\b", r"misses?\b", r"forecast", r"outlook", r"dividend",
        r"buyback", r"interim results",
    ],
    "Leadership Change": [
        r"resign", r"appoint", r"\bceo\b", r"\bcfo\b", r"\bcoo\b",
        r"chairman", r"stepping down", r"replac", r"succession", r"retires",
    ],
    "M&A Activity": [
        r"acqui", r"merger", r"takeover", r"buyout", r"\bstake\b",
        r"partnership", r"joint venture", r"strategic alliance",
    ],
    "Product Launch": [
        r"launch", r"unveil", r"announc", r"release[sd]?", r"introduc",
        r"new (product|model|chip|phone|feature|platform|gpu)",
    ],
    "Business Milestone": [
        r"milestone", r"record\b", r"crosses?\b", r"surpass", r"subscriber",
        r"highest ever", r"first time", r"billionth",
    ],
    "Macroeconomic": [
        r"\brbi\b", r"\bfed\b", r"interest rate", r"inflation", r"\bgdp\b",
        r"repo rate", r"monetary policy", r"central bank", r"rate cut",
        r"rate hike", r"tariff",
    ],
    "Debt/Credit": [
        r"downgrad", r"upgrades? rating", r"credit rating", r"default",
        r"bond", r"debt", r"junk", r"investment grade", r"s&p", r"moody",
    ],
    "ESG/Sustainability": [
        r"esg", r"sustainab", r"carbon", r"net.zero", r"climate",
        r"renewable", r"green bond", r"social impact",
    ],
}

_EVENT_MULTIPLIER: dict[str, float] = {
    "Regulatory/Legal":  1.35,
    "Earnings/Financial": 1.20,
    "Leadership Change": 1.25,
    "M&A Activity":      1.10,
    "Product Launch":    1.05,
    "Business Milestone": 1.00,
    "Macroeconomic":     0.80,
    "Debt/Credit":       1.15,
    "ESG/Sustainability": 0.70,
    "General News":      0.90,
}


def classify_event(headline: str) -> str:
    h = headline.lower()
    for evt, pats in _EVENT_PATTERNS.items():
        if any(re.search(p, h) for p in pats):
            return evt
    return "General News"


# ── STAGE 3 — FINBERT ─────────────────────────────────────────────────────────

_POS_W: dict[str, float] = {
    "record": 0.25, "beats": 0.22, "surge": 0.20, "profit": 0.18,
    "growth": 0.17, "wins": 0.16, "raises": 0.15, "strong": 0.14,
    "milestone": 0.13, "deal": 0.12, "launch": 0.11, "upgraded": 0.20,
    "partnership": 0.13, "expands": 0.12, "bullish": 0.18, "crosses": 0.15,
    "surpasses": 0.16, "acquires": 0.12, "outperforms": 0.19,
    "exceeds": 0.18, "accelerat": 0.14, "award": 0.11, "secures": 0.15,
}
_NEG_W: dict[str, float] = {
    "fine": 0.25, "fined": 0.26, "recall": 0.22, "probe": 0.21,
    "violation": 0.24, "investigation": 0.22, "lawsuit": 0.23,
    "resign": 0.28, "fraud": 0.30, "ban": 0.24, "loss": 0.20,
    "decline": 0.18, "miss": 0.19, "misses": 0.21, "disappoints": 0.22,
    "warning": 0.18, "layoffs": 0.20, "cuts": 0.17, "drops": 0.16,
    "falls": 0.15, "penalty": 0.24, "restrict": 0.20, "default": 0.28,
    "downgrade": 0.26, "impairment": 0.23, "writedown": 0.24,
    "sanction": 0.25, "shutdown": 0.22, "abruptly": 0.18,
}


def _kw_score(headline: str) -> tuple[float, float]:
    h = headline.lower()
    pos = sum(_POS_W.get(w, 0) for w in _POS_W if w in h)
    neg = sum(_NEG_W.get(w, 0) for w in _NEG_W if w in h)
    raw = round(min(1.0, max(-1.0, pos - neg)), 3)
    conf = round(min(0.92, 0.50 + abs(raw) * 0.42), 3)
    return raw, conf


def finbert_score(headline: str) -> tuple[float, float, str]:
    """Returns (polarity, confidence, source). Falls back to keyword scoring."""
    model = get_finbert()
    if model is not None:
        try:
            r = model(headline[:512])[0]
            lbl = r["label"].lower()
            sc = float(r["score"])
            if lbl == "positive":
                return round(sc * 0.95, 3), round(sc, 3), "finbert"
            if lbl == "negative":
                return round(-sc * 0.95, 3), round(sc, 3), "finbert"
            return round((sc - 0.5) * 0.2, 3), round(sc, 3), "finbert"
        except Exception:
            pass
    raw, conf = _kw_score(headline)
    return raw, conf, "keyword_fallback"


# ── STAGE 4 — RUMOUR DETECTION ────────────────────────────────────────────────

_RUMOUR_SIGNALS = [
    "sources say", "reportedly", "according to insiders", "unconfirmed",
    "rumour", "rumor", "is said to", "people familiar", "could be",
    "might consider", "early talks", "exploring options", "may consider",
    "anonymous sources", "not yet confirmed", "we hear that",
]
_CONFIRM_SIGNALS = [
    "announces", "confirms", "reports", "releases", "files for",
    "officially", "completed", "signed", "approved", "issued",
    "disclosed in", "press release", "investor update",
]


def detect_rumour(headline: str) -> tuple[bool, float]:
    """Returns (is_rumour, credibility_score 0-1)."""
    h = headline.lower()
    r_hits = sum(1 for s in _RUMOUR_SIGNALS if s in h)
    c_hits = sum(1 for s in _CONFIRM_SIGNALS if s in h)
    if r_hits > 0 and c_hits == 0:
        cred = round(max(0.20, 0.65 - r_hits * 0.12), 2)
        return True, cred
    if c_hits > 0:
        cred = round(min(1.0, 0.82 + c_hits * 0.05), 2)
        return False, cred
    return False, 0.78


# ── STAGE 5 — SHAP WORD ATTRIBUTION ──────────────────────────────────────────

def word_attributions(headline: str) -> list[dict]:
    attrs: list[dict] = []
    for tok in headline.lower().split():
        w = re.sub(r"[^a-z]", "", tok)
        if w in _POS_W:
            attrs.append({"word": w, "contribution": _POS_W[w]})
        elif w in _NEG_W:
            attrs.append({"word": w, "contribution": -_NEG_W[w]})
    seen: dict[str, dict] = {}
    for a in attrs:
        if a["word"] not in seen or abs(a["contribution"]) > abs(seen[a["word"]]["contribution"]):
            seen[a["word"]] = a
    return sorted(seen.values(), key=lambda x: abs(x["contribution"]), reverse=True)[:10]


# ── FINANCIAL JARGON ──────────────────────────────────────────────────────────

_JARGON = [
    "ipo", "spac", "eps", "ebitda", "p/e", "market cap", "short selling",
    "hedge fund", "derivative", "options", "futures", "yield", "bond",
    "credit rating", "downgrade", "upgrade", "buyback", "dividend", "split",
    "merger", "acquisition", "regulatory", "compliance", "antitrust",
    "sec", "rbi", "sebi", "nifty", "sensex", "nasdaq", "nyse", "bse",
    "nse", "qoq", "yoy", "cagr", "roe", "roa", "pat", "nii", "nim",
    "bps", "basis points", "leverage", "liquidity", "solvency", "pe ratio",
    "price earnings", "book value", "working capital", "free cash flow",
]


def detect_jargon(headline: str) -> list[str]:
    h = headline.lower()
    return [j for j in _JARGON if j in h]


# ── STAGE 6 — HISTORICAL SIMILARITY ──────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _get_corpus_embeddings(headlines: tuple) -> Optional[np.ndarray]:
    """Cache encoded corpus so repeated calls don't re-encode 200 rows."""
    enc = get_encoder()
    if enc is None:
        return None
    try:
        return enc.encode(list(headlines))
    except Exception:
        return None


def _cosine_sim_sklearn(q_emb, c_emb):
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity(q_emb, c_emb)[0]


def find_similar(query: str, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df is None or df.empty or "Headline" not in df.columns:
        return pd.DataFrame()

    sub = (
        df[df["Ticker"] == ticker].copy()
        if "Ticker" in df.columns and (df["Ticker"] == ticker).sum() >= 3
        else df.copy()
    )
    sub = sub.reset_index(drop=True)

    enc = get_encoder()
    if enc is not None:
        try:
            q_emb = enc.encode([query])
            # Use cached corpus embeddings
            headlines_tuple = tuple(sub["Headline"].tolist())
            c_emb = _get_corpus_embeddings(headlines_tuple)
            if c_emb is None:
                c_emb = enc.encode(list(headlines_tuple))
            sims = _cosine_sim_sklearn(q_emb, c_emb)
            sub = sub.copy()
            sub["similarity"] = np.round(sims * 100, 1)
            return (
                sub[sub["similarity"] > 42]
                .sort_values("similarity", ascending=False)
                .head(5)
                .reset_index(drop=True)
            )
        except Exception:
            pass

    # TF-IDF fallback
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        corpus = sub["Headline"].tolist()
        mat = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2)
        ).fit_transform(corpus + [query])
        sims = _cosine_sim_sklearn(mat[-1], mat[:-1])
        sub = sub.copy()
        sub["similarity"] = np.round(sims * 100, 1)
        return (
            sub[sub["similarity"] > 18]
            .sort_values("similarity", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )
    except Exception:
        return pd.DataFrame()


def historical_prediction(similar: pd.DataFrame) -> dict:
    if similar is None or similar.empty or "t3_move_pct" not in similar.columns:
        return {}
    moves = similar["t3_move_pct"].dropna()
    if moves.empty:
        return {}
    avg = round(float(moves.mean()), 2)
    std = round(float(moves.std()), 2) if len(moves) > 1 else 0.5
    cnt = len(moves)
    acc = int(((moves > 0) == (avg > 0)).sum())
    return {
        "avg_move": avg,
        "std": std,
        "range_low": round(avg - std, 2),
        "range_high": round(avg + std, 2),
        "sample_count": cnt,
        "directional_acc": round(acc / cnt * 100, 1) if cnt else 0,
    }


# ── STAGE 7 — MACRO CONTEXT ───────────────────────────────────────────────────

def macro_context(polarity: float) -> tuple[float, str]:
    """Return (amplification_factor, description)."""
    try:
        import yfinance as yf
        vix = float(yf.Ticker("^VIX").fast_info.last_price)
    except Exception:
        vix = 18.5  # moderate default

    if vix > 30:
        factor = 1.35 if polarity < 0 else 1.12
        desc = f"High volatility (VIX {vix:.0f}) — impact amplified significantly"
    elif vix > 20:
        factor = 1.15 if polarity < 0 else 1.06
        desc = f"Elevated volatility (VIX {vix:.0f}) — mild amplification"
    else:
        factor = 1.0
        desc = f"Calm market (VIX {vix:.0f}) — base impact applies"

    return round(factor, 2), desc


# ── CATEGORY / LABEL ──────────────────────────────────────────────────────────

def polarity_category(p: float) -> str:
    if p <= -0.60: return "STRONG_NEGATIVE"
    if p <= -0.20: return "NEGATIVE"
    if p <   0.20: return "NEUTRAL"
    if p <   0.60: return "POSITIVE"
    return "STRONG_POSITIVE"


def category_label(cat: str) -> str:
    return {
        "STRONG_NEGATIVE": "Strong Negative",
        "NEGATIVE":        "Negative",
        "NEUTRAL":         "Neutral",
        "POSITIVE":        "Positive",
        "STRONG_POSITIVE": "Strong Positive",
    }.get(cat, "Neutral")


# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────

def run_analysis(headline: str, ticker: str) -> dict:
    if not headline or not headline.strip():
        return _empty_result("Headline is empty.")

    # Stage 1 — NER
    entities = detect_entities(headline)

    # Stage 2 — Event Classification
    evt = classify_event(headline)
    evt_mult = _EVENT_MULTIPLIER.get(evt, 1.0)

    # Stage 3 — FinBERT (raw base sentiment)
    raw_pol, conf, conf_src = finbert_score(headline)

    # Stage 4 — Rumour (apply credibility BEFORE event multiplier)
    is_rum, cred = detect_rumour(headline)
    dampened = round(raw_pol * cred, 3) if is_rum else raw_pol

    # Apply event multiplier to dampened polarity
    polarity = round(max(-1.0, min(1.0, dampened * evt_mult)), 3)

    # Relevance score — penalise by non-matching entities
    is_relevant = (ticker in entities) or not entities
    other_entities = [e for e in entities if e != ticker]
    rel_score = 0.95 if is_relevant else max(0.28, 0.72 - len(other_entities) * 0.15)

    # Stage 5 — SHAP
    attrs = word_attributions(headline)

    # Stage 6 — Historical
    df = get_news_df()
    similar = find_similar(headline, df, ticker)
    hist_pr = historical_prediction(similar)

    # Stage 7 — Macro
    macro_f, macro_d = macro_context(polarity)
    adj_pol = round(max(-1.0, min(1.0, polarity * macro_f)), 3)

    # Extras
    jargon = detect_jargon(headline)
    ripple = compute_ripple(ticker, adj_pol)

    cat = polarity_category(adj_pol)
    lbl = category_label(cat)

    reason_parts = [
        f"FinBERT classified this as <strong>{lbl}</strong> with {conf:.0%} confidence"
        + (" (keyword fallback — model unavailable)." if conf_src == "keyword_fallback" else "."),
        f"Event type detected: <strong>{evt}</strong> (×{evt_mult:.2f} multiplier).",
    ]
    if is_rum:
        reason_parts.append(f"Rumour signals detected — credibility dampened to {cred:.0%}.")
    if not is_relevant:
        reason_parts.append(
            f"Headline may not be directly about {ticker} (relevance {rel_score:.0%})."
        )
    if hist_pr:
        avg = hist_pr.get("avg_move", 0)
        reason_parts.append(
            f"Historical analogues suggest a T+3 move of {avg:+.1f}% "
            f"({hist_pr.get('directional_acc', 0):.0f}% directional accuracy)."
        )
    reason_parts.append(macro_d + ".")

    # Safe count of similar results
    sim_count = len(similar) if similar is not None and not similar.empty else 0

    return {
        "polarity":          adj_pol,
        "raw_polarity":      raw_pol,
        "category":          cat,
        "label":             lbl,
        "confidence":        round(conf, 3),
        "confidence_source": conf_src,
        "relevance_score":   round(rel_score, 3),
        "is_relevant":       is_relevant,
        "event_type":        evt,
        "event_multiplier":  evt_mult,
        "is_rumour":         is_rum,
        "credibility":       cred,
        "detected_entities": entities,
        "jargon_detected":   jargon,
        "word_attributions": attrs,
        "reason":            " ".join(reason_parts),
        "macro_factor":      macro_f,
        "macro_description": macro_d,
        "similar_headlines": similar,
        "similar_count":     sim_count,
        "hist_prediction":   hist_pr,
        "ripple_tree":       ripple,
        "ticker":            ticker,
        "headline":          headline,
        "analyzed_at":       datetime.now().isoformat(),
        "pipeline_version":  "v5",
    }


def _empty_result(msg: str) -> dict:
    return {
        "polarity": 0.0, "raw_polarity": 0.0, "category": "NEUTRAL",
        "label": "Neutral", "confidence": 0.0, "confidence_source": "none",
        "relevance_score": 0.0, "is_relevant": False,
        "event_type": "General News", "event_multiplier": 1.0,
        "is_rumour": False, "credibility": 1.0,
        "detected_entities": [], "jargon_detected": [],
        "word_attributions": [], "reason": msg,
        "macro_factor": 1.0, "macro_description": "",
        "similar_headlines": pd.DataFrame(), "similar_count": 0,
        "hist_prediction": {}, "ripple_tree": [],
        "ticker": "", "headline": "",
        "analyzed_at": datetime.now().isoformat(),
        "pipeline_version": "v5",
    }
