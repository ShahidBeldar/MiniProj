"""
app.py — FinanceImpact entry point.
FIX: pages/6_Market.py now registered in st.navigation() — fixes 404 on Streamlit Cloud.
FIX: Sidebar removed from app.py — every page calls render_sidebar() itself, avoiding duplication.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Finance Impact",
    layout="wide",
    initial_sidebar_state="collapsed",  # JS in render_sidebar() opens it on load
)

from ui.auth import bootstrap, is_logged_in, render_login_page, do_logout
from ui.theme import inject_css
from core.seeder import ensure_sample_data

bootstrap()
ensure_sample_data()
inject_css()

if not is_logged_in():
    render_login_page()
    st.stop()

# Register ALL pages — required for Streamlit Cloud routing
pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Home.py",      title="Home",      default=True),
        ],
        "Tools": [
            st.Page("pages/1_Dashboard.py", title="Analyzer"),
            st.Page("pages/2_News.py",      title="News Feed"),
            st.Page("pages/3_Watchlist.py", title="Watchlist"),
            st.Page("pages/4_History.py",   title="History"),
            st.Page("pages/6_Market.py",    title="Market"),
        ],
        "Account": [
            st.Page("pages/5_Settings.py",  title="Settings"),
        ],
    },
    position="hidden",   # custom sidebar nav used instead
)

pg.run()
