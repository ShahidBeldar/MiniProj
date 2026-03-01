"""
app.py — Finance Impact entry point.
- st.navigation() registers all pages (makes st.page_link work on Cloud)
- position="hidden" suppresses built-in nav so we control the full sidebar
- Sidebar is rendered in ONE block after pg = st.navigation(...)
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

# ── REGISTER PAGES — must happen before any sidebar rendering ─────────────────
pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Home.py",      title="Home",     icon="🏠", default=True),
        ],
        "Tools": [
            st.Page("pages/1_Dashboard.py", title="Analyzer", icon="📡"),
            st.Page("pages/2_News.py",      title="News Feed", icon="📰"),
            st.Page("pages/3_Watchlist.py", title="Watchlist", icon="📊"),
            st.Page("pages/4_History.py",   title="History",   icon="🕐"),
        ],
        "Account": [
            st.Page("pages/5_Settings.py",  title="Settings",  icon="⚙️"),
        ],
    },
    position="hidden",  # We own the full sidebar
)

# ── SIDEBAR — single block, full control ─────────────────────────────────────
_un   = uname()
_init = _un[0].upper() if _un else "?"

_NAV = [
    ("🏠", "Home",     "pages/0_Home.py"),
    ("📡", "Analyzer", "pages/1_Dashboard.py"),
    ("📰", "News Feed","pages/2_News.py"),
    ("📊", "Watchlist","pages/3_Watchlist.py"),
    ("🕐", "History",  "pages/4_History.py"),
    ("⚙️", "Settings", "pages/5_Settings.py"),
]

with st.sidebar:
    # Logo
    st.markdown(f"""
        <div style="padding:1.2rem 1rem .7rem;border-bottom:1px solid #1A2535;margin-bottom:.6rem;">
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.28rem;
                        color:#DDE6F0;letter-spacing:-.012em;line-height:1.1;">
                Finance<span style="color:#00C8F0;">Impact</span>
            </div>
            <div style="font-family:'Manrope',sans-serif;font-size:.54rem;color:#3D5268;
                        letter-spacing:.22em;text-transform:uppercase;margin-top:4px;">
                Market Intelligence
            </div>
        </div>
    """, unsafe_allow_html=True)

    # User chip
    st.markdown(f"""
        <div style="display:flex;align-items:center;gap:9px;padding:8px 10px;
                    background:#0F1520;border-radius:10px;border:1px solid #1A2535;
                    margin:0 .4rem .9rem;">
            <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        display:flex;align-items:center;justify-content:center;
                        font-size:11px;font-weight:700;font-family:'Syne',sans-serif;color:#fff;">
                {_init}
            </div>
            <div>
                <div style="font-family:'Manrope',sans-serif;font-size:.8rem;
                            font-weight:600;color:#DDE6F0;">{_un}</div>
                <div style="font-size:.55rem;color:#3D5268;letter-spacing:.1em;
                            font-family:'Manrope',sans-serif;">SIGNED IN</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Nav links — st.page_link works because pages are registered above
    for icon_e, label, page_path in _NAV:
        st.page_link(page_path, label=f"{icon_e}  {label}", use_container_width=True)

    # Divider + sign-out
    st.markdown(
        '<div style="height:1px;background:#1A2535;margin:.8rem .4rem .5rem;"></div>',
        unsafe_allow_html=True,
    )
    if st.button("⏻  Sign Out", key="_sb_signout", use_container_width=True, type="secondary"):
        do_logout()
        st.rerun()

pg.run()
