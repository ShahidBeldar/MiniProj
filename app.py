"""
app.py — Finance Impact entry point.
Uses st.navigation() + st.Page() for Cloud-safe multi-page routing.
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

from ui.auth     import bootstrap, is_logged_in, render_login_page, do_logout, uname
from ui.theme    import inject_css
from core.seeder import ensure_sample_data

bootstrap()
ensure_sample_data()
inject_css()

# ── AUTH GATE ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_login_page()
    st.stop()

# ── REGISTER ALL PAGES WITH st.navigation() ───────────────────────────────────
# This is what makes st.switch_page() work on Streamlit Cloud —
# pages must be registered here before they can be switched to.
pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Home.py",       title="Home",       icon="🏠", default=True),
        ],
        "Analysis": [
            st.Page("pages/1_Dashboard.py",  title="Dashboard",  icon="📡"),
            st.Page("pages/6_Market.py",     title="Market",     icon="📈"),
            st.Page("pages/2_News.py",       title="News Feed",  icon="📰"),
        ],
        "Portfolio": [
            st.Page("pages/3_Watchlist.py",  title="Watchlist",  icon="📊"),
            st.Page("pages/4_History.py",    title="History",    icon="🕐"),
        ],
        "Account": [
            st.Page("pages/5_Settings.py",   title="Settings",   icon="⚙️"),
        ],
    },
    position="hidden",   # We render our own sidebar nav
)
pg.run()
