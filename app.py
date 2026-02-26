"""
app.py — Finance Impact entry point.
Handles bootstrap, auth gate, and sidebar navigation.
Run with: streamlit run app.py
"""

import streamlit as st

# ── PAGE CONFIG (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Finance Impact",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── BOOTSTRAP ─────────────────────────────────────────────────────────────────
from utils.auth import bootstrap, is_logged_in, render_login_page, logout, current_username
from utils.styles import inject_styles
from utils.sample_data import ensure_sample_data

bootstrap()           # init DB + seed users
ensure_sample_data()  # generate news.csv if missing
inject_styles()       # global CSS

# ── AUTH GATE ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_login_page()
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            Finance<span>Impact</span>
        </div>
        <div style="font-size:0.68rem;color:#3D5268;letter-spacing:0.15em;
                    text-transform:uppercase;margin-bottom:1.5rem;">
            Market Intelligence
        </div>
    """, unsafe_allow_html=True)

    # User info
    uname = current_username()
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;
                    padding:10px 12px;background:#111927;border-radius:10px;
                    border:1px solid #1A2535;margin-bottom:1rem;">
            <div style="width:30px;height:30px;border-radius:50%;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        display:flex;align-items:center;justify-content:center;
                        font-size:12px;font-weight:700;font-family:'Syne',sans-serif;">
                {uname[0].upper()}
            </div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:12px;
                            font-weight:600;color:#DDE6F0;">{uname}</div>
                <div style="font-size:9px;color:#3D5268;letter-spacing:0.1em;">
                    SIGNED IN
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    st.page_link("app.py",               label="🏠 Home",          )
    st.page_link("pages/1_dashboard.py", label="⚡ Dashboard")
    st.page_link("pages/2_news_feed.py", label="📰 News Feed")
    st.page_link("pages/3_watchlist.py", label="📊 Watchlist")
    st.page_link("pages/4_history.py",   label="🕐 History")
    st.page_link("pages/5_settings.py",  label="⚙️ Settings")

    st.markdown("---")

    if st.button("Sign Out", key="sidebar_logout", use_container_width=True, type="secondary"):
        logout()

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
st.markdown("""
    <h1 style='font-family:Syne,sans-serif;font-weight:800;font-size:2rem;
               letter-spacing:-0.02em;margin-bottom:0.25rem;'>
        Finance<span style='color:#00C8F0;'>Impact</span>
    </h1>
    <p style='color:#3D5268;font-size:0.8rem;letter-spacing:0.12em;
              text-transform:uppercase;margin-bottom:2rem;'>
        Market Intelligence Platform
    </p>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="fi-card">
            <div style="font-size:1.8rem;margin-bottom:0.75rem;">⚡</div>
            <div class="fi-card-title">Headline Analyzer</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                Analyze any financial headline through our 7-stage ML pipeline —
                FinBERT sentiment, event classification, rumour detection,
                SHAP explainability, and corporate ripple effect.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_dashboard.py", label="Open Dashboard →")

with col2:
    st.markdown("""
        <div class="fi-card">
            <div style="font-size:1.8rem;margin-bottom:0.75rem;">🌐</div>
            <div class="fi-card-title">Corporate Ripple Effect</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                See how news propagates through a company's entire subsidiary tree.
                Impact decays by ownership %, relationship type, and depth —
                across 10 major Indian and US companies.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="fi-card">
            <div style="font-size:1.8rem;margin-bottom:0.75rem;">📰</div>
            <div class="fi-card-title">Live News Feed</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                Live financial headlines from Reuters, Bloomberg, ET Markets,
                and more via RSS — auto-tagged with ticker and pre-scored
                for sentiment. Click any headline to analyze instantly.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_news_feed.py", label="Open Feed →")

st.markdown("<br>", unsafe_allow_html=True)

# Quick stats
from utils.database import get_user_stats
from utils.auth import current_user_id
uid   = current_user_id()
stats = get_user_stats(uid) if uid else {}

s1, s2, s3, s4 = st.columns(4)
with s1:
    st.metric("Analyses Run",    stats.get("total", 0))
with s2:
    st.metric("Tickers Covered", stats.get("unique_tickers", 0))
with s3:
    st.metric("Positive Signals", stats.get("positive", 0))
with s4:
    conf = stats.get("avg_confidence", 0)
    st.metric("Avg Confidence", f"{conf:.0%}" if conf else "—")
