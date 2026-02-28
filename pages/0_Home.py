"""
pages/0_Home.py — Home / landing page.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

from ui.theme      import inject_css
from ui.auth       import require_login, uid as get_uid, do_logout, uname
from ui.nav        import render_sidebar
from ui.components import page_header
from db.ops        import get_stats

inject_css()
require_login()
render_sidebar("home")

_uid   = get_uid()
_stats = get_stats(_uid) if _uid else {}

# ── HEADER + LOGOUT ───────────────────────────────────────────────────────────
hdr_col, logout_col = st.columns([6, 1])
with hdr_col:
    st.markdown(page_header(
        'Finance<span style="color:#00C8F0;">Impact</span>',
        "Market Intelligence Platform · 7-stage ML pipeline · Live Charts · Corporate Ripple"
    ), unsafe_allow_html=True)
with logout_col:
    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    if st.button("⏻  Sign Out", key="_home_logout", type="secondary", use_container_width=True):
        do_logout()
        st.rerun()

# ── FEATURE CARDS ─────────────────────────────────────────────────────────────
_cards = [
    ("Headline Analyzer",
     "7-stage ML pipeline — FinBERT sentiment, event classification, SHAP attribution, "
     "rumour detection, historical similarity, and corporate ripple effect propagation.",
     "pages/1_Dashboard.py", "Open Dashboard →", "#00C8F0"),
    ("Market Analysis",
     "Live global indices, candlestick & line charts, technical indicators (RSI, MACD, "
     "Bollinger Bands, VWAP, ATR), multi-ticker comparison, and correlation heatmap.",
     "pages/6_Market.py", "Open Market →", "#9B6DFF"),
    ("Portfolio Watchlist",
     "Track your tickers with live prices, latest sentiment signals, day change bars, "
     "90-day normalised chart, and one-click analysis routing to the Dashboard.",
     "pages/3_Watchlist.py", "Open Watchlist →", "#00E8A0"),
    ("Live News Feed",
     "RSS headlines from Reuters, Bloomberg, ET Markets, Moneycontrol, CNBC and more — "
     "auto-scored, ticker-tagged, rumour-flagged, and click-to-analyze.",
     "pages/2_News.py", "Open News Feed →", "#FFD060"),
]

row1 = st.columns(2)
row2 = st.columns(2)
for col, (title, body, pg, lbl, accent) in zip([row1[0], row1[1], row2[0], row2[1]], _cards):
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
        if st.button(lbl, key=f"_home_{pg}", use_container_width=True, type="secondary"):
            st.switch_page(pg)

st.markdown("<br>", unsafe_allow_html=True)

# ── STATS ─────────────────────────────────────────────────────────────────────
total   = _stats.get("total",    0)
tickers = _stats.get("tickers",  0)
pos     = _stats.get("positive", 0)
neg     = _stats.get("negative", 0)
conf    = _stats.get("avg_conf") or 0

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Analyses Run",    total)
with m2: st.metric("Tickers Covered", tickers)
with m3: st.metric("Bullish Signals", pos)
with m4: st.metric("Bearish Signals", neg)
with m5: st.metric("Avg Confidence",  f"{conf:.0%}" if conf else "—")

st.markdown("<br>", unsafe_allow_html=True)

# ── QUICK ACCESS ──────────────────────────────────────────────────────────────
st.markdown('<div class="fi-section">Quick Access</div>', unsafe_allow_html=True)
q1, q2, q3, q4, q5 = st.columns(5)
_quick = [
    (q1, "pages/1_Dashboard.py", "Analyze Headline"),
    (q2, "pages/6_Market.py",    "Market Charts"),
    (q3, "pages/2_News.py",      "News Feed"),
    (q4, "pages/3_Watchlist.py", "My Watchlist"),
    (q5, "pages/4_History.py",   "History"),
]
for col, pg, lbl in _quick:
    with col:
        if st.button(lbl, key=f"_hq_{pg}", use_container_width=True):
            st.switch_page(pg)

st.markdown("<br>", unsafe_allow_html=True)

# ── ML PIPELINE STAGES ────────────────────────────────────────────────────────
st.markdown('<div class="fi-section">ML Pipeline Stages</div>', unsafe_allow_html=True)
cols = st.columns(7)
stages = [
    "1 · NER|Entity detection|#00C8F0",
    "2 · Event|Event classification|#9B6DFF",
    "3 · FinBERT|Financial sentiment|#00E8A0",
    "4 · Rumour|Credibility scoring|#FFD060",
    "5 · SHAP|Word attribution|#FF7D35",
    "6 · Historical|Similarity search|#00C8F0",
    "7 · Macro|VIX amplification|#9B6DFF",
]
for col, s in zip(cols, stages):
    title, desc, color = s.split("|")
    with col:
        st.markdown(f"""
            <div class="fi-card" style="text-align:center;padding:.8rem .6rem;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.72rem;
                            color:{color};margin-bottom:4px;">{title}</div>
                <div style="font-size:.62rem;color:#3D5268;font-family:'Manrope',sans-serif;
                            line-height:1.4;">{desc}</div>
            </div>
        """, unsafe_allow_html=True)
