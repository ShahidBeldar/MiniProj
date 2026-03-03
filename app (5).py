"""
app.py — Finance Impact entry point.
Sidebar uses plain HTML <a> links — works on Streamlit Cloud and locally.
URL paths: Streamlit Cloud derives them from filenames (strips number prefix + underscores).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import streamlit as st

st.set_page_config(
    page_title="Finance Impact",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.auth     import bootstrap, is_logged_in, render_login_page, do_logout, uname
from ui.theme    import inject_css
from core.seeder import ensure_sample_data

bootstrap()
ensure_sample_data()
inject_css()

if not is_logged_in():
    render_login_page()
    st.stop()

# Register all pages — required for Streamlit Cloud page routing
pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Home.py",      title="Home",     default=True),
        ],
        "Tools": [
            st.Page("pages/1_Dashboard.py", title="Analyzer"),
            st.Page("pages/2_News.py",      title="News Feed"),
            st.Page("pages/3_Watchlist.py", title="Watchlist"),
            st.Page("pages/4_History.py",   title="History"),
        ],
        "Account": [
            st.Page("pages/5_Settings.py",  title="Settings"),
        ],
    },
    position="hidden",
)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
_un   = uname()
_init = _un[0].upper() if _un else "?"

# Detect current page from URL path
_path  = st.context.headers.get("X-Forwarded-For", "")
try:
    _curr = st.query_params.get("_page", "")
except Exception:
    _curr = ""

_NAV = [
    ("🏠", "Home",      "/"),
    ("📡", "Analyzer",  "/Analyzer"),
    ("📰", "News Feed", "/News_Feed"),
    ("📊", "Watchlist", "/Watchlist"),
    ("🕐", "History",   "/History"),
    ("⚙️", "Settings",  "/Settings"),
]

nav_links_html = ""
for icon_e, label, href in _NAV:
    nav_links_html += f"""
        <a href="{href}" target="_self" class="fi-nav-link">
            <span class="fi-nav-icon">{icon_e}</span>
            <span class="fi-nav-label">{label}</span>
        </a>
    """

with st.sidebar:
    st.markdown(f"""
        <div class="fi-sidebar-logo">
            <div class="fi-logo-text">Finance<span style="color:#00C8F0;">Impact</span></div>
            <div class="fi-logo-sub">Market Intelligence</div>
        </div>

        <div class="fi-user-chip">
            <div class="fi-avatar">{_init}</div>
            <div>
                <div class="fi-username">{_un}</div>
                <div class="fi-role">SIGNED IN</div>
            </div>
        </div>

        <nav class="fi-nav">
            {nav_links_html}
        </nav>

        <div class="fi-sidebar-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("⏻  Sign Out", key="_sb_signout", use_container_width=True, type="secondary"):
        do_logout()
        st.rerun()

pg.run()
