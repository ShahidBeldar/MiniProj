"""
pages/5_Settings.py — User settings, profile, security, data management, about.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

st.set_page_config(page_title="Settings · Finance Impact", layout="wide", initial_sidebar_state="expanded")

from ui.theme   import inject_css
from ui.auth    import require_login, current_user, uid, do_change_password
from ui.nav     import render_sidebar
from ui.components import page_header, badge, mini_progress_bar
from db.ops     import get_settings, save_settings, get_stats, clear_history
from core.graph import get_tickers

inject_css()
require_login()
st.session_state["_page"] = "settings"
render_sidebar("settings")

_uid  = uid()
user  = current_user()
sett  = get_settings(_uid)
stats = get_stats(_uid)

st.markdown(page_header(
    'Settings <span style="color:#00C8F0;">&amp; Profile</span>',
    "Account info · analysis preferences · security · data management",
), unsafe_allow_html=True)

tab_p, tab_pr, tab_s, tab_d, tab_ab = st.tabs(
    ["Profile", "Preferences", "Security", "Data", "About"]
)


# ════════ PROFILE ════════════════════════════════════════════════════════════
with tab_p:
    _un    = user.get("username", "")
    _email = user.get("email", "") or "Not set"
    _role  = user.get("role", "user").title()
    av_col, info_col = st.columns([1, 3])

    with av_col:
        st.markdown(f"""
            <div style="text-align:center;">
                <div style="width:88px;height:88px;border-radius:50%;margin:0 auto;
                            background:linear-gradient(135deg,#667eea,#764ba2);
                            display:flex;align-items:center;justify-content:center;
                            font-size:2rem;font-weight:700;font-family:'Syne',sans-serif;
                            color:#fff;border:3px solid #22334A;">
                    {_un[0].upper() if _un else "?"}
                </div>
                <div style="margin-top:10px;font-family:'Syne',sans-serif;font-weight:700;
                            font-size:.88rem;color:#DDE6F0;">{_un}</div>
                <div style="margin-top:4px;">{badge(_role, "accent" if _role=="Admin" else "neutral")}</div>
            </div>
        """, unsafe_allow_html=True)

    with info_col:
        total = stats.get("total", 0) or 1
        st.markdown(f"""
            <div class="fi-card">
                <div class="fi-title">Account Info</div>
                <table style="width:100%;border-collapse:collapse;font-size:.8rem;">
                    {''.join(
                        f'<tr style="border-bottom:1px solid #1A2535;">'
                        f'<td style="padding:7px 0;color:#3D5268;width:38%;font-family:Manrope,sans-serif;">{k}</td>'
                        f'<td style="padding:7px 0;color:{vc};font-family:Manrope,sans-serif;">{v}</td></tr>'
                        for k,v,vc in [
                            ("Username",        _un,                           "#DDE6F0"),
                            ("Email",           _email,                        "#DDE6F0"),
                            ("Role",            _role,                         "#00C8F0"),
                            ("Analyses Run",    str(stats.get("total",0)),     "#DDE6F0"),
                            ("Tickers Tracked", str(stats.get("tickers",0)),   "#DDE6F0"),
                            ("Avg Confidence",  f"{(stats.get('avg_conf') or 0):.0%}", "#DDE6F0"),
                        ]
                    )}
                </table>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="fi-section">Analysis Breakdown</div>', unsafe_allow_html=True)
    for lbl2, cnt, color in [
        ("Bullish",  stats.get("positive",0), "#00E8A0"),
        ("Bearish",  stats.get("negative",0), "#FF3D60"),
        ("Neutral",  stats.get("neutral",0),  "#7A92A8"),
    ]:
        pct = cnt / total
        st.markdown(mini_progress_bar(f"{lbl2}  ({cnt})", pct, color), unsafe_allow_html=True)


# ════════ PREFERENCES ════════════════════════════════════════════════════════
with tab_pr:
    st.markdown('<div class="fi-card"><div class="fi-title">Analysis Defaults</div>',
                unsafe_allow_html=True)
    available = get_tickers()
    cur_def   = sett.get("default_ticker", "TSLA")
    def_idx   = available.index(cur_def) if cur_def in available else 0
    new_def   = st.selectbox("Default Ticker on Dashboard", available, index=def_idx, key="_sp_dt")
    show_conf = st.toggle("Show Confidence Breakdown",   value=bool(sett.get("show_confidence",1)), key="_sp_sc")
    show_rip  = st.toggle("Show Corporate Ripple Effect",value=bool(sett.get("show_ripple",1)),     key="_sp_sr")
    show_hist = st.toggle("Show Historical Matches",     value=bool(sett.get("show_history",1)),    key="_sp_sh")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Preferences", type="primary", key="_sp_save"):
        save_settings(_uid, {
            "default_ticker":  new_def,
            "show_confidence": 1 if show_conf else 0,
            "show_ripple":     1 if show_rip  else 0,
            "show_history":    1 if show_hist else 0,
        })
        st.success("Preferences saved successfully.")


# ════════ SECURITY ═══════════════════════════════════════════════════════════
with tab_s:
    st.markdown('<div class="fi-card"><div class="fi-title">Change Password</div>',
                unsafe_allow_html=True)
    with st.form("_cpw_form", clear_on_submit=True):
        old_p = st.text_input("Current Password",        type="password", key="_cpw_old")
        new_p = st.text_input("New Password (min 6)",    type="password", key="_cpw_new")
        cnf_p = st.text_input("Confirm New Password",    type="password", key="_cpw_cnf")
        cpw_b = st.form_submit_button("Update Password",  type="primary")
    if cpw_b:
        ok, msg = do_change_password(_uid, old_p, new_p, cnf_p)
        st.success(msg) if ok else st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)


# ════════ DATA MANAGEMENT ════════════════════════════════════════════════════
with tab_d:
    st.markdown('<div class="fi-card"><div class="fi-title">Data Management</div>',
                unsafe_allow_html=True)

    st.markdown(f"""
        <div style="font-size:.8rem;color:#7A92A8;margin-bottom:1rem;
                    font-family:'Manrope',sans-serif;line-height:1.65;">
            You have <strong style="color:#DDE6F0;">{stats.get('total',0)}</strong> saved analyses.
            Clearing history is permanent and cannot be undone.
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Export All History (CSV)", type="secondary",
                     use_container_width=True, key="_dm_exp"):
            from db.ops import get_history as gh
            import pandas as pd
            rows = gh(_uid, limit=9999)
            if rows:
                df_exp = pd.DataFrame([{
                    "Date":       h.get("analyzed_at","")[:19].replace("T"," "),
                    "Ticker":     h["ticker"],
                    "Headline":   h["headline"],
                    "Polarity":   h.get("polarity",0),
                    "Category":   h.get("category",""),
                    "Confidence": h.get("confidence",0),
                    "EventType":  h.get("event_type",""),
                } for h in rows])
                csv = df_exp.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data=csv,
                                   file_name="fi_history_export.csv",
                                   mime="text/csv", key="_dm_dl")
            else:
                st.info("No data to export.")

    with col_b:
        if st.button("Clear All History", type="secondary",
                     use_container_width=True, key="_dm_clr"):
            st.session_state["_confirm_clear"] = True

    if st.session_state.get("_confirm_clear"):
        st.warning("This will permanently delete all your analysis history.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Confirm — Delete All", type="primary",  key="_dm_yes", use_container_width=True):
                clear_history(_uid)
                st.session_state.pop("_confirm_clear", None)
                st.success("History cleared.")
                st.rerun()
        with cc2:
            if st.button("Cancel",                type="secondary", key="_dm_no",  use_container_width=True):
                st.session_state.pop("_confirm_clear", None)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ════════ ABOUT ══════════════════════════════════════════════════════════════
with tab_ab:
    st.markdown("""
        <div class="fi-card">
            <div class="fi-title">Platform Information</div>
            <table style="width:100%;border-collapse:collapse;font-size:.8rem;">
    """ + "".join(
        f'<tr style="border-bottom:1px solid #1A2535;">'
        f'<td style="padding:7px 0;color:#3D5268;width:38%;font-family:Manrope,sans-serif;">{k}</td>'
        f'<td style="padding:7px 0;color:#DDE6F0;font-family:Manrope,sans-serif;">{v}</td></tr>'
        for k, v in [
            ("ML Model",         "ProsusAI/FinBERT — financial sentiment analysis"),
            ("Sentence Encoder", "all-MiniLM-L6-v2 — semantic similarity search"),
            ("Event Types",      "9 categories: Regulatory, Earnings, Leadership, M&A, Product, Milestone, Macro, Debt, ESG"),
            ("Corporate Graph",  "NetworkX — ownership-weighted 3-level subsidiary ripple propagation"),
            ("Price Data",       "yFinance — 5-min cache, Indian NSE ticker support"),
            ("News Sources",     "Reuters, Bloomberg, ET Markets, Moneycontrol, CNBC, Yahoo, Livemint, Seeking Alpha"),
            ("Database",         "SQLite with WAL mode — users, history, watchlist, settings"),
            ("Architecture",     "core/ (pure Python) · db/ (SQLite) · ui/ (Streamlit) · pages/ (5 pages)"),
            ("Framework",        "Python 3.11+ · Streamlit · Plotly · Syne + Manrope + JetBrains Mono"),
            ("Version",          "v4 — Enhanced architecture, clean separation of concerns"),
        ]
    ) + """
            </table>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="fi-card" style="margin-top:.85rem;">
            <div class="fi-title">Session State Architecture</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:.72rem;
                        color:#7A92A8;line-height:1.9;">
                <span style="color:#00C8F0;">_fi_loggedin</span>  → auth flag (bool)<br>
                <span style="color:#00C8F0;">_fi_user</span>      → user dict {id, username, email, role}<br>
                <span style="color:#FFD060;">_dash_hl</span>      → dashboard headline widget key<br>
                <span style="color:#FFD060;">_dash_t</span>       → dashboard ticker widget key<br>
                <span style="color:#FF7D35;">_pending_hl</span>   → pre-fill staging (flushed before widgets)<br>
                <span style="color:#FF7D35;">_pending_t</span>    → pre-fill staging (flushed before widgets)<br>
                <span style="color:#00E8A0;">_result</span>       → latest analysis dict (24+ fields)<br>
            </div>
        </div>
    """, unsafe_allow_html=True)
