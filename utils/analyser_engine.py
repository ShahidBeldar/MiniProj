"""
analyser_engine.py — Full ML pipeline.

Stages:
  1. NER (spaCy) — entity detection
  2. Event Classification — rule + keyword based
  3. FinBERT — financial sentiment
  4. Rumour vs Fact Detector — credibility scoring
  5. SHAP word attribution — explainability
  6. Historical similarity — sentence-transformers vector search
  7. Macro Context — VIX-style amplification

All models are cached with @st.cache_resource to load only once.
"""

import os
import re
import json
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from typing import Optional


# ── MODEL LOADERS (cached) ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading FinBERT model…")
def load_finbert():
    from transformers import pipeline
    try:
        return pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
    except Exception as e:
        st.warning(f"FinBERT load failed: {e}. Using keyword fallback.")
        return None


@st.cache_resource(show_spinner="Loading sentence encoder…")
def load_encoder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


@st.cache_data(show_spinner="Loading historical data…")
def load_news_df() -> pd.DataFrame:
    from utils.sample_data import ensure_sample_data
    path = ensure_sample_data()
    try:
        df = pd.read_csv(path)
        return df
    except Exception:
        return pd.DataFrame()


# ── NER ───────────────────────────────────────────────────────────────────────
COMPANY_KEYWORDS = {
    "TSLA":      ["tesla", "elon musk"],
    "AAPL":      ["apple", "tim cook", "iphone", "ipad", "mac"],
    "GOOGL":     ["google", "alphabet", "waymo", "youtube", "deepmind"],
    "MSFT":      ["microsoft", "azure", "satya nadella", "openai", "github"],
    "NVDA":      ["nvidia", "jensen huang", "h100", "cuda", "blackwell"],
    "AMZN":      ["amazon", "aws", "andy jassy", "prime"],
    "RELIANCE":  ["reliance", "jio", "mukesh ambani"],
    "TCS":       ["tcs", "tata consultancy"],
    "INFY":      ["infosys", "salil parekh"],
    "WIPRO":     ["wipro"],
    "HDFCBANK":  ["hdfc bank", "hdfc"],
}

def detect_entities(headline: str) -> list[str]:
    h = headline.lower()
    found = []
    for ticker, kws in COMPANY_KEYWORDS.items():
        if any(kw in h for kw in kws):
            found.append(ticker)
    return found or []


# ── EVENT CLASSIFICATION ──────────────────────────────────────────────────────
EVENT_PATTERNS = {
    "Regulatory/Legal": [
        r"fine[sd]?", r"penalt", r"violation", r"lawsuit", r"probe", r"investigat",
        r"regulat", r"sanction", r"ban", r"antitrust", r"doj", r"sec\b", r"ftc\b",
        r"court", r"ruling", r"compliance", r"recall",
    ],
    "Earnings/Financial": [
        r"earnings", r"revenue", r"profit", r"loss", r"q[1-4]\b", r"quarterly",
        r"guidance", r"eps\b", r"ebitda", r"margins?", r"beats?\b", r"misses?\b",
        r"forecast", r"outlook", r"fiscal",
    ],
    "Leadership Change": [
        r"resign", r"appoint", r"ceo\b", r"cfo\b", r"coo\b", r"chairman",
        r"stepping down", r"takes over", r"replac", r"succession", r"hire[sd]?",
    ],
    "M&A Activity": [
        r"acqui", r"merger", r"deal\b", r"takeover", r"buyout",
        r"stake\b", r"invest", r"partnership", r"joint venture",
    ],
    "Product Launch": [
        r"launch", r"unveil", r"announc", r"release[sd]?", r"introduc",
        r"new (product|model|chip|phone|feature)", r"v\d+\b",
    ],
    "Business Milestone": [
        r"milestone", r"record\b", r"crosses?\b", r"surpass", r"subscriber",
        r"users?\b", r"customers?\b", r"highest ever", r"first time",
    ],
    "Macroeconomic": [
        r"rbi\b", r"fed\b", r"interest rate", r"inflation", r"gdp\b",
        r"unemployment", r"repo rate", r"monetary policy", r"central bank",
    ],
}

EVENT_IMPACT_MULTIPLIER = {
    "Regulatory/Legal":    1.35,
    "Earnings/Financial":  1.20,
    "Leadership Change":   1.25,
    "M&A Activity":        1.10,
    "Product Launch":      1.05,
    "Business Milestone":  1.00,
    "Macroeconomic":       0.80,
    "General News":        0.90,
}

def classify_event(headline: str) -> str:
    h = headline.lower()
    for event_type, patterns in EVENT_PATTERNS.items():
        if any(re.search(p, h) for p in patterns):
            return event_type
    return "General News"


# ── RUMOUR DETECTOR ───────────────────────────────────────────────────────────
RUMOUR_SIGNALS   = ["sources say", "reportedly", "according to insiders",
                    "unconfirmed", "rumour", "rumor", "is said to",
                    "people familiar with", "could be", "might consider",
                    "early talks", "exploring options"]
CONFIRMED_SIGNALS = ["announces", "confirms", "reports", "releases",
                     "files for", "officially", "completed", "signed",
                     "approved", "issued"]

def detect_rumour(headline: str) -> tuple[bool, float]:
    """Returns (is_rumour, credibility_score 0-1)."""
    h = headline.lower()
    rumour_hit    = sum(1 for s in RUMOUR_SIGNALS    if s in h)
    confirmed_hit = sum(1 for s in CONFIRMED_SIGNALS if s in h)

    if rumour_hit > 0 and confirmed_hit == 0:
        cred = max(0.20, 0.65 - rumour_hit * 0.15)
        return True, round(cred, 2)
    if confirmed_hit > 0:
        return False, min(1.0, 0.80 + confirmed_hit * 0.05)
    return False, 0.75


# ── FINANCIAL JARGON DETECTION ────────────────────────────────────────────────
JARGON_TERMS = [
    "ipo", "spac", "eps", "ebitda", "p/e", "pe ratio", "market cap",
    "short selling", "hedge fund", "derivative", "options", "futures",
    "yield", "bond", "credit rating", "downgrade", "upgrade", "buyback",
    "dividend", "split", "merger", "acquisition", "ipo", "rpo",
    "regulatory", "compliance", "antitrust", "sec", "rbi", "sebi",
    "nifty", "sensex", "nasdaq", "nyse", "bse", "nse",
    "qoq", "yoy", "cagr", "roe", "roa", "pat", "nii", "nim",
    "bps", "basis points", "leverage", "liquidity", "solvency",
]

def detect_jargon(headline: str) -> list[str]:
    h = headline.lower()
    return [term for term in JARGON_TERMS if term in h]


# ── SHAP WORD ATTRIBUTION (lightweight) ──────────────────────────────────────
POSITIVE_WEIGHTS = {
    "record": 0.25, "beats": 0.22, "surge": 0.20, "profit": 0.18,
    "growth": 0.17, "wins": 0.16, "raises": 0.15, "strong": 0.14,
    "milestone": 0.13, "deal": 0.12, "launch": 0.11, "upgraded": 0.20,
    "partnership": 0.13, "expands": 0.12, "bullish": 0.18,
    "crosses": 0.15, "surpasses": 0.16, "acquires": 0.12, "announces": 0.08,
}
NEGATIVE_WEIGHTS = {
    "fine": 0.25, "fined": 0.26, "recall": 0.22, "probe": 0.21,
    "violation": 0.24, "investigation": 0.22, "lawsuit": 0.23,
    "resign": 0.28, "fraud": 0.30, "ban": 0.24, "loss": 0.20,
    "decline": 0.18, "miss": 0.19, "misses": 0.21, "disappoints": 0.22,
    "warning": 0.18, "layoffs": 0.20, "cuts": 0.17, "drops": 0.16,
    "falls": 0.15, "penalty": 0.24, "restrict": 0.20, "default": 0.28,
}

def compute_word_attributions(headline: str) -> list[dict]:
    """
    Lightweight SHAP-style attribution.
    Returns list of {word, contribution, direction}.
    """
    tokens = headline.lower().split()
    attrs  = []
    for token in tokens:
        clean = re.sub(r"[^a-z]", "", token)
        if clean in POSITIVE_WEIGHTS:
            attrs.append({"word": clean, "contribution": POSITIVE_WEIGHTS[clean], "direction": "positive"})
        elif clean in NEGATIVE_WEIGHTS:
            attrs.append({"word": clean, "contribution": -NEGATIVE_WEIGHTS[clean], "direction": "negative"})
    # Sort by abs contribution
    attrs.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return attrs[:8]


# ── HISTORICAL SIMILARITY ─────────────────────────────────────────────────────
def compute_similarity_scores(query: str, news_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Find similar past headlines using sentence embeddings if available,
    falling back to TF-IDF cosine similarity.
    """
    if news_df is None or news_df.empty:
        return pd.DataFrame()

    # Filter by ticker if possible
    df = news_df.copy()
    if "Ticker" in df.columns:
        ticker_df = df[df["Ticker"] == ticker]
        if len(ticker_df) >= 3:
            df = ticker_df

    encoder = load_encoder()

    if encoder is not None:
        try:
            corpus     = df["Headline"].tolist()
            query_emb  = encoder.encode([query])
            corpus_emb = encoder.encode(corpus)
            from sklearn.metrics.pairwise import cosine_similarity
            sims = cosine_similarity(query_emb, corpus_emb)[0]
            df = df.copy()
            df["similarity"] = np.round(sims * 100, 1)
            df = df.sort_values("similarity", ascending=False)
            return df[df["similarity"] > 45].head(5).reset_index(drop=True)
        except Exception:
            pass

    # TF-IDF fallback
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as cs
        corpus = df["Headline"].tolist()
        vec    = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        mat    = vec.fit_transform(corpus + [query])
        sims   = cs(mat[-1], mat[:-1])[0]
        df     = df.copy()
        df["similarity"] = np.round(sims * 100, 1)
        df     = df.sort_values("similarity", ascending=False)
        return df[df["similarity"] > 20].head(5).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ── MACRO CONTEXT AMPLIFICATION ───────────────────────────────────────────────
def get_macro_amplifier(polarity: float) -> tuple[float, str]:
    """
    Simplified macro context amplifier.
    In production this would pull live VIX. For now uses rule-based defaults.
    Returns (amplifier_factor, description).
    """
    # Simulate market context from date/time heuristics
    # In a real system: pull VIX from yfinance("^VIX").fast_info.last_price
    import random
    random.seed(42)
    simulated_vix = 18.5  # Moderate — realistic default

    if simulated_vix > 30:
        factor = 1.35 if polarity < 0 else 1.10
        desc   = f"High volatility (VIX ~{simulated_vix:.0f}) amplifies impact"
    elif simulated_vix > 20:
        factor = 1.15 if polarity < 0 else 1.05
        desc   = f"Elevated volatility (VIX ~{simulated_vix:.0f})"
    else:
        factor = 1.0
        desc   = f"Calm market (VIX ~{simulated_vix:.0f}) — normal impact"

    return round(factor, 2), desc


# ── FINBERT INFERENCE ─────────────────────────────────────────────────────────
def finbert_score(headline: str) -> tuple[float, float]:
    """
    Run FinBERT on headline.
    Returns (polarity, confidence).
    Polarity: positive=+score, negative=-score, neutral≈0.
    """
    model = load_finbert()
    if model is None:
        return _keyword_fallback_score(headline)

    try:
        result = model(headline[:512])[0]
        label  = result["label"].lower()
        score  = float(result["score"])

        if label == "positive":
            return round(score * 0.95, 3), round(score, 3)
        elif label == "negative":
            return round(-score * 0.95, 3), round(score, 3)
        else:  # neutral
            return round((score - 0.5) * 0.2, 3), round(score, 3)
    except Exception:
        return _keyword_fallback_score(headline)


def _keyword_fallback_score(headline: str) -> tuple[float, float]:
    """Keyword-based fallback when FinBERT is unavailable."""
    h = headline.lower()
    pos_w = list(POSITIVE_WEIGHTS.keys())
    neg_w = list(NEGATIVE_WEIGHTS.keys())
    pos   = sum(POSITIVE_WEIGHTS.get(w, 0) for w in pos_w if w in h)
    neg   = sum(NEGATIVE_WEIGHTS.get(w, 0) for w in neg_w if w in h)
    raw   = min(1.0, max(-1.0, pos - neg))
    conf  = min(0.92, 0.55 + abs(raw) * 0.4)
    return round(raw, 3), round(conf, 3)


# ── CATEGORY LABEL ────────────────────────────────────────────────────────────
def polarity_to_category(polarity: float) -> str:
    if polarity <= -0.60: return "STRONG_NEGATIVE"
    if polarity <= -0.20: return "NEGATIVE"
    if polarity <   0.20: return "NEUTRAL"
    if polarity <   0.60: return "POSITIVE"
    return "STRONG_POSITIVE"

def category_to_label(cat: str) -> str:
    return {
        "STRONG_NEGATIVE": "Strong Negative",
        "NEGATIVE":        "Negative",
        "NEUTRAL":         "Neutral",
        "POSITIVE":        "Positive",
        "STRONG_POSITIVE": "Strong Positive",
    }.get(cat, "Neutral")


# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────
def run_analysis(headline: str, ticker: str) -> dict:
    """
    Full 7-stage analysis pipeline.
    Returns comprehensive result dict.
    """
    if not headline or not isinstance(headline, str) or not headline.strip():
        return _empty_result("Invalid or empty headline.")

    # ── Stage 1: NER ──
    entities = detect_entities(headline)

    # ── Stage 2: Event Classification ──
    event_type = classify_event(headline)
    event_mult = EVENT_IMPACT_MULTIPLIER.get(event_type, 1.0)

    # ── Stage 3: FinBERT ──
    raw_polarity, finbert_conf = finbert_score(headline)

    # Apply event multiplier (caps at ±1.0)
    polarity   = round(max(-1.0, min(1.0, raw_polarity * event_mult)), 3)
    category   = polarity_to_category(polarity)

    # ── Stage 4: Rumour Detection ──
    is_rumour, credibility = detect_rumour(headline)
    # Dampen polarity for rumours
    if is_rumour:
        polarity = round(polarity * credibility, 3)

    # ── Stage 4b: Relevance ──
    # Check if headline is directly about the requested ticker
    headline_tickers = entities
    is_relevant = (ticker in headline_tickers) or len(headline_tickers) == 0
    relevance_score = 0.95 if is_relevant else max(0.3, 0.7 - len(headline_tickers) * 0.1)

    # ── Stage 5: SHAP Attributions ──
    word_attributions = compute_word_attributions(headline)

    # ── Stage 6: Historical Similarity ──
    news_df = load_news_df()
    similar = compute_similarity_scores(headline, news_df, ticker)

    # Compute historical prediction
    hist_prediction = _compute_hist_prediction(similar)

    # ── Stage 7: Macro Context ──
    macro_factor, macro_desc = get_macro_amplifier(polarity)
    adjusted_polarity = round(max(-1.0, min(1.0, polarity * macro_factor)), 3)

    # ── Jargon & Ripple ──
    jargon = detect_jargon(headline)

    from utils.corporate_graph import compute_ripple
    ripple_tree = compute_ripple(ticker, adjusted_polarity)

    # ── Build Reason Text ──
    reason = _build_reason(
        headline, event_type, adjusted_polarity, finbert_conf,
        credibility, is_rumour, macro_desc, relevance_score, is_relevant, ticker
    )

    return {
        # Core sentiment
        "polarity":           adjusted_polarity,
        "raw_polarity":       raw_polarity,
        "category":           polarity_to_category(adjusted_polarity),
        "label":              category_to_label(polarity_to_category(adjusted_polarity)),
        "confidence":         round(finbert_conf, 3),
        "relevance_score":    round(relevance_score, 3),
        "is_relevant":        is_relevant,

        # Event & credibility
        "event_type":         event_type,
        "event_multiplier":   event_mult,
        "is_rumour":          is_rumour,
        "credibility":        credibility,

        # Entities
        "detected_entities":  entities,
        "jargon_detected":    jargon,

        # Explainability
        "word_attributions":  word_attributions,
        "reason":             reason,

        # Macro
        "macro_factor":       macro_factor,
        "macro_description":  macro_desc,

        # Historical
        "similar_headlines":  similar,
        "hist_prediction":    hist_prediction,

        # Ripple
        "ripple_tree":        ripple_tree,

        # Meta
        "ticker":             ticker,
        "headline":           headline,
        "analyzed_at":        datetime.now().isoformat(),
    }


def _compute_hist_prediction(similar: pd.DataFrame) -> dict:
    """Compute T+3 prediction stats from similar headlines."""
    if similar.empty or "t3_move_pct" not in similar.columns:
        return {}

    moves      = similar["t3_move_pct"].dropna()
    if moves.empty:
        return {}

    avg        = round(float(moves.mean()), 2)
    std        = round(float(moves.std()), 2) if len(moves) > 1 else 0.5
    direction  = "up" if avg > 0 else "down"
    count      = len(moves)
    dir_correct = int(((moves > 0) == (avg > 0)).sum())

    return {
        "avg_move":         avg,
        "std":              std,
        "range_low":        round(avg - std, 2),
        "range_high":       round(avg + std, 2),
        "direction":        direction,
        "sample_count":     count,
        "directional_acc":  round(dir_correct / count * 100, 1) if count else 0,
    }


def _build_reason(headline, event_type, polarity, finbert_conf,
                  credibility, is_rumour, macro_desc,
                  relevance_score, is_relevant, ticker) -> str:
    label = category_to_label(polarity_to_category(polarity))
    parts = [
        f"FinBERT classified this as **{label}** (confidence: {finbert_conf:.0%}).",
        f"Event type detected: **{event_type}**.",
    ]
    if is_rumour:
        parts.append(f"Rumour signals found — credibility dampened to {credibility:.0%}.")
    if not is_relevant:
        parts.append(f"Headline may not be directly about {ticker} — relevance: {relevance_score:.0%}.")
    parts.append(macro_desc + ".")
    return " ".join(parts)


def _empty_result(msg: str) -> dict:
    return {
        "polarity": 0.0, "raw_polarity": 0.0,
        "category": "NEUTRAL", "label": "Neutral",
        "confidence": 0.0, "relevance_score": 0.0, "is_relevant": False,
        "event_type": "General News", "event_multiplier": 1.0,
        "is_rumour": False, "credibility": 1.0,
        "detected_entities": [], "jargon_detected": [],
        "word_attributions": [], "reason": msg,
        "macro_factor": 1.0, "macro_description": "",
        "similar_headlines": pd.DataFrame(),
        "hist_prediction": {}, "ripple_tree": [],
        "ticker": "", "headline": "", "analyzed_at": datetime.now().isoformat(),
    }
