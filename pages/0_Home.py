"""
pages/0_Home.py — Home / landing page.
FIX: Replaced all <a href> navigation with st.button + st.switch_page so session
     state (_fi_loggedin) is preserved across page transitions on Streamlit Cloud.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from ui.theme import inject_css
from ui.auth import require_login, uid as get_uid
from ui.nav import render_sidebar
from ui.components import page_header
from db.ops import get_stats

inject_css()
require_login()
render_sidebar("home")

_uid = get_uid()

@st.cache_data(ttl=120)
def _stats(u: int) -> dict:
    return get_stats(u)

_stats_data = _stats(_uid) if _uid else {}

# ── HEADER ────────────────────────────────────────────────────────────────────

st.markdown(page_header(
    'Finance<span style="color:#00C8F0;">Impact</span>',
    "Market Intelligence Platform · 7-stage ML pipeline · Live Charts · Corporate Ripple",
), unsafe_allow_html=True)

# ── FEATURE CARDS ─────────────────────────────────────────────────────────────

_cards = [
    (
        "Headline Analyzer",
        "7-stage ML pipeline — FinBERT sentiment, event classification, SHAP attribution, "
        "rumour detection, historical similarity, and corporate ripple effect propagation.",
        "pages/1_Dashboard.py", "Open Dashboard →", "#00C8F0",
    ),
    (
        "Portfolio Watchlist",
        "Track your tickers with live prices, latest sentiment signals, day change bars, "
        "90-day normalised chart, and one-click analysis routing to the Dashboard.",
        "pages/3_Watchlist.py", "Open Watchlist →", "#00E8A0",
    ),
    (
        "Live News Feed",
        "RSS headlines from Reuters, Bloomberg, ET Markets, Moneycontrol, CNBC and more — "
        "auto-scored, ticker-tagged, rumour-flagged, and click-to-analyze.",
        "pages/2_News.py", "Open News Feed →", "#FFD060",
    ),
]

card_cols = st.columns(3)
for col, (title, body, page_path, lbl, accent) in zip(card_cols, _cards):
    with col:
        st.markdown(f"""
        <div class="fi-card" style="border-top:2px solid {accent};min-height:120px;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.92rem;
                      color:#DDE6F0;margin-bottom:.45rem;display:flex;align-items:center;gap:8px;">
            <span style="width:7px;height:7px;border-radius:50%;background:{accent};
                         flex-shrink:0;box-shadow:0 0 6px {accent};display:inline-block;"></span>
            {title}
          </div>
          <div style="font-family:'Manrope',sans-serif;font-size:.75rem;
                      color:#7A92A8;line-height:1.72;margin-bottom:.8rem;">{body}</div>
        </div>
        """, unsafe_allow_html=True)
        # FIX: st.button + st.switch_page preserves session state (no full browser nav)
        if st.button(lbl, key=f"_home_card_{page_path}", use_container_width=True, type="secondary"):
            st.switch_page(page_path)

st.markdown("<br>", unsafe_allow_html=True)

# ── STATS ─────────────────────────────────────────────────────────────────────

total   = _stats_data.get("total", 0)
tickers = _stats_data.get("tickers", 0)
pos     = _stats_data.get("positive", 0)
neg     = _stats_data.get("negative", 0)
conf    = _stats_data.get("avg_conf") or 0

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Analyses Run",    total)
with m2: st.metric("Tickers Covered", tickers)
with m3: st.metric("Bullish Signals", pos)
with m4: st.metric("Bearish Signals", neg)
with m5: st.metric("Avg Confidence",  f"{conf:.0%}" if conf else "—")

st.markdown("<br>", unsafe_allow_html=True)

# ── QUICK ACCESS ──────────────────────────────────────────────────────────────

st.markdown('<div class="fi-section">Quick Access</div>', unsafe_allow_html=True)
q1, q2, q3, q4, q5, q6 = st.columns(6)
_quick = [
    (q1, "pages/1_Dashboard.py", "Analyze Headline"),
    (q2, "pages/2_News.py",      "News Feed"),
    (q3, "pages/3_Watchlist.py", "My Watchlist"),
    (q4, "pages/4_History.py",   "History"),
    (q5, "pages/6_Market.py",    "Market"),
    (q6, "pages/5_Settings.py",  "Settings"),
]
for col, page_path, lbl in _quick:
    with col:
        # FIX: st.button preserves session state; <a href> caused logout on Streamlit Cloud
        if st.button(lbl, key=f"_home_quick_{page_path}", use_container_width=True, type="secondary"):
            st.switch_page(page_path)

st.markdown("<br>", unsafe_allow_html=True)

# ── ML PIPELINE STAGES ────────────────────────────────────────────────────────

st.markdown('<div class="fi-section">ML Pipeline — v5</div>', unsafe_allow_html=True)
cols = st.columns(7)
stages = [
    ("1 · NER",        "Entity detection",      "#00C8F0"),
    ("2 · Event",      "Event classification",  "#9B6DFF"),
    ("3 · FinBERT",    "Financial sentiment",   "#00E8A0"),
    ("4 · Rumour",     "Credibility scoring",   "#FFD060"),
    ("5 · SHAP",       "Word attribution",      "#FF7D35"),
    ("6 · Historical", "Similarity search",     "#00C8F0"),
    ("7 · Macro",      "VIX amplification",     "#9B6DFF"),
]
for col, (title, desc, color) in zip(cols, stages):
    with col:
        st.markdown(f"""
        <div class="fi-card" style="text-align:center;padding:.8rem .6rem;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.72rem;
                      color:{color};margin-bottom:4px;">{title}</div>
          <div style="font-size:.62rem;color:#3D5268;font-family:'Manrope',sans-serif;
                      line-height:1.4;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
