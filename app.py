"""
app.py — Finance Impact entry point.
Run: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Finance Impact",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.auth    import bootstrap, is_logged_in, render_login_page
from ui.theme   import inject_css
from ui.nav     import render_sidebar
from core.seeder import ensure_sample_data
from db.ops     import get_stats
from ui.components import (
    page_header, badge, stat_box, stat_row, sentiment_color, sentiment_badge_kind
)

bootstrap()
ensure_sample_data()
inject_css()

if not is_logged_in():
    render_login_page()
    st.stop()

render_sidebar("home")

# ── IMPORTS NEEDED ONLY AFTER AUTH ────────────────────────────────────────────
from ui.auth import uid as get_uid
_uid   = get_uid()
_stats = get_stats(_uid) if _uid else {}

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
st.markdown(page_header(
    'Finance<span style="color:#00C8F0;">Impact</span>',
    "Market Intelligence Platform · 7-stage ML pipeline · Corporate Ripple Effect"
), unsafe_allow_html=True)

# Feature cards
c1, c2, c3 = st.columns(3)
_cards = [
    (c1, "dashboard",
     "Headline Analyzer",
     "7-stage ML pipeline — FinBERT sentiment, event classification, SHAP attribution, "
     "rumour detection, historical similarity, and corporate ripple effect propagation.",
     "pages/1_Dashboard.py", "Open Dashboard"),
    (c2, "watchlist",
     "Portfolio Watchlist",
     "Track your tickers with live prices, latest sentiment signals, day change bars, "
     "and one-click analysis routing to the Dashboard.",
     "pages/3_Watchlist.py", "Open Watchlist"),
    (c3, "news",
     "Live News Feed",
     "RSS headlines from Reuters, Bloomberg, ET Markets, Moneycontrol, CNBC and more — "
     "auto-scored, ticker-tagged, and click-to-analyze.",
     "pages/2_News.py", "Open News Feed"),
]
for col, icon_k, title, body, pg, lbl in _cards:
    with col:
        st.markdown(f"""
            <div class="fi-card">
                <div class="fi-title">{title}</div>
                <div style="font-family:'Manrope',sans-serif;font-size:.76rem;
                            color:#7A92A8;line-height:1.72;margin-bottom:.75rem;">{body}</div>
            </div>
        """, unsafe_allow_html=True)
        st.page_link(pg, label=lbl)

st.markdown("<br>", unsafe_allow_html=True)

# Stats row
total   = _stats.get("total",    0)
tickers = _stats.get("tickers",  0)
pos     = _stats.get("positive", 0)
conf    = _stats.get("avg_conf") or 0
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Analyses Run",     total)
with m2: st.metric("Tickers Covered",  tickers)
with m3: st.metric("Positive Signals", pos)
with m4: st.metric("Avg Confidence",   f"{conf:.0%}" if conf else "—")

# Pipeline stages info
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="fi-section">ML Pipeline Stages</div>', unsafe_allow_html=True)
p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
stages = [
    (p1, "1 · NER",            "Entity detection",         "#00C8F0"),
    (p2, "2 · Event",          "Event classification",     "#9B6DFF"),
    (p3, "3 · FinBERT",        "Financial sentiment",      "#00E8A0"),
    (p4, "4 · Rumour",         "Credibility scoring",      "#FFD060"),
    (p5, "5 · SHAP",           "Word attribution",         "#FF7D35"),
    (p6, "6 · Historical",     "Similarity search",        "#00C8F0"),
    (p7, "7 · Macro",          "VIX amplification",        "#9B6DFF"),
]
for col, title, desc, color in stages:
    with col:
        st.markdown(f"""
            <div class="fi-card" style="text-align:center;padding:.8rem .6rem;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.72rem;
                            color:{color};margin-bottom:4px;">{title}</div>
                <div style="font-size:.62rem;color:#3D5268;font-family:'Manrope',sans-serif;
                            line-height:1.4;">{desc}</div>
            </div>
        """, unsafe_allow_html=True)
