"""
app.py — Finance Impact entry point.
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Finance Impact",
    page_icon="assets/favicon.png" if False else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.auth     import bootstrap, is_logged_in, render_login_page, logout, current_username
from utils.styles   import inject_styles, icon, nav_link_html
from utils.sample_data import ensure_sample_data
from utils.db       import get_user_stats
from utils.auth     import current_user_id

bootstrap()
ensure_sample_data()
inject_styles()

# ── AUTH GATE ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_login_page()
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
        <div style="padding:1.25rem 0.75rem 0.75rem;">
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.25rem;
                        color:#DDE6F0;letter-spacing:-0.01em;">
                Finance<span style="color:#00C8F0;">Impact</span>
            </div>
            <div style="font-size:0.62rem;color:#3D5268;letter-spacing:0.18em;
                        text-transform:uppercase;margin-top:3px;">
                Market Intelligence
            </div>
        </div>
    """, unsafe_allow_html=True)

    # User chip
    uname = current_username()
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:9px;
                    padding:9px 12px;background:#111927;border-radius:10px;
                    border:1px solid #1A2535;margin:0.5rem 0.25rem 1rem;">
            <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        display:flex;align-items:center;justify-content:center;
                        font-size:11px;font-weight:700;font-family:'Syne',sans-serif;
                        color:#fff;">
                {uname[0].upper()}
            </div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:0.78rem;
                            font-weight:600;color:#DDE6F0;">{uname}</div>
                <div style="font-size:0.6rem;color:#3D5268;letter-spacing:0.1em;">
                    SIGNED IN
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:0 0.25rem;">', unsafe_allow_html=True)

    # Detect current page for active state
    current_page = st.session_state.get("_current_page", "home")

    nav_items = [
        ("home",      "Home",      "app.py"),
        ("dashboard", "Dashboard", "pages/dashboard.py"),
        ("news",      "News Feed", "pages/news.py"),
        ("watchlist", "Watchlist", "pages/watchlist.py"),
        ("history",   "History",   "pages/history.py"),
        ("settings",  "Settings",  "pages/settings.py"),
    ]

    for key, label, page in nav_items:
        active = current_page == key
        color  = "#00C8F0" if active else "#7A92A8"
        bg     = "background:rgba(0,200,240,0.07);border:1px solid rgba(0,200,240,0.2);" if active else "border:1px solid transparent;"
        ico    = icon(key, color)
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;
                        padding:9px 12px;border-radius:8px;margin-bottom:2px;
                        {bg}cursor:pointer;">
                {ico}
                <span style="font-family:'DM Mono',monospace;font-size:0.82rem;
                             color:{color};">{label}</span>
            </div>
        """, unsafe_allow_html=True)
        st.page_link(page, label=" ", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:#1A2535;margin:0.75rem 0;"></div>',
                unsafe_allow_html=True)

    if st.button("Sign Out", key="sidebar_signout", use_container_width=True, type="secondary"):
        logout()

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
st.session_state["_current_page"] = "home"

st.markdown("""
    <div style="margin-bottom:2rem;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:2rem;
                    letter-spacing:-0.02em;color:#DDE6F0;">
            Finance<span style="color:#00C8F0;">Impact</span>
        </div>
        <div style="font-size:0.72rem;color:#3D5268;letter-spacing:0.15em;
                    text-transform:uppercase;margin-top:4px;">
            Market Intelligence Platform
        </div>
    </div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
        <div class="fi-card">
            <div class="fi-card-title">Headline Analyzer</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                Analyze any financial headline through the 7-stage ML pipeline —
                FinBERT sentiment, event classification, rumour detection,
                SHAP explainability, and corporate ripple effect.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/dashboard.py", label="Open Dashboard")

with c2:
    st.markdown("""
        <div class="fi-card">
            <div class="fi-card-title">Corporate Ripple Effect</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                See how news propagates through a company's entire subsidiary tree.
                Impact decays by ownership percentage, relationship type, and depth
                across 10 major Indian and US companies.
            </div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
        <div class="fi-card">
            <div class="fi-card-title">Live News Feed</div>
            <div style="font-size:0.78rem;color:#7A92A8;line-height:1.65;">
                Live financial headlines from Reuters, Bloomberg, ET Markets,
                and more via RSS — auto-tagged with ticker and pre-scored
                for sentiment. Click any headline to analyze instantly.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/news.py", label="Open Feed")

st.markdown("<br>", unsafe_allow_html=True)

uid   = current_user_id()
stats = get_user_stats(uid) if uid else {}

s1, s2, s3, s4 = st.columns(4)
with s1: st.metric("Analyses Run",     stats.get("total", 0))
with s2: st.metric("Tickers Covered",  stats.get("unique_tickers", 0))
with s3: st.metric("Positive Signals", stats.get("positive", 0))
with s4:
    conf = stats.get("avg_confidence") or 0
    st.metric("Avg Confidence", f"{conf:.0%}" if conf else "—")
