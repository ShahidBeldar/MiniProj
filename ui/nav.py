"""
ui/nav.py — Shared sidebar with fully clickable st.button() navigation.
Call render_sidebar(current_page) at the top of every page.

Navigation pattern:
  - st.button(type="primary")  for active page  → cyan highlight
  - st.button(type="secondary") for inactive     → transparent
  - st.switch_page(path) on click
"""
from __future__ import annotations
import streamlit as st
from ui.auth  import is_logged_in, uname, do_logout
from ui.theme import icon


_PAGES = [
    ("home",      "Home",       "app.py",                "home"),
    ("dashboard", "Dashboard",  "pages/1_Dashboard.py",  "dashboard"),
    ("news",      "News Feed",  "pages/2_News.py",       "news"),
    ("watchlist", "Watchlist",  "pages/3_Watchlist.py",  "watchlist"),
    ("history",   "History",    "pages/4_History.py",    "history"),
    ("settings",  "Settings",   "pages/5_Settings.py",   "settings"),
]


def render_sidebar(current: str = "home") -> None:
    if not is_logged_in():
        return

    _un   = uname()
    _init = (_un[0].upper()) if _un else "?"

    with st.sidebar:
        # ── Logo ────────────────────────────────────────────────────────────
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

        # ── User chip ────────────────────────────────────────────────────────
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

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown('<div style="padding:0 .3rem;">', unsafe_allow_html=True)
        for key, label, pg, page_key in _PAGES:
            active   = (current == page_key)
            ic_color = "#00C8F0" if active else "#7A92A8"
            btn_type = "primary" if active else "secondary"
            # Inline icon via markdown positioned above button
            st.markdown(
                f'<div style="position:absolute;pointer-events:none;z-index:1;'
                f'padding:9px 0 0 13px;">{icon(key, ic_color)}</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f"   {label}",
                key=f"_nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.switch_page(pg)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Divider + sign-out ────────────────────────────────────────────────
        st.markdown(
            '<div style="height:1px;background:#1A2535;margin:.8rem .4rem .5rem;"></div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", key="_nav_signout", use_container_width=True, type="secondary"):
            do_logout()
