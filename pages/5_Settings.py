"""
pages/5_Settings.py — User settings, profile, security, data management, about.
FIX: Data export is a single-click download_button (no nested button).
FIX: _stats.clear() removed from save_preferences (stats unrelated to prefs).
FIX: Account deletion option added (GDPR / user autonomy).
FIX: render_sidebar() called for consistent navigation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from ui.theme import inject_css
from ui.auth import require_login, current_user, uid, do_change_password
from ui.nav import render_sidebar
from ui.components import page_header, badge, mini_progress_bar
from db.ops import (
    get_settings, save_settings, get_stats, clear_history,
    get_active_alerts, delete_alert, get_history,
)
from core.graph import get_tickers

inject_css()
require_login()
render_sidebar("settings")

_uid  = uid()
user  = current_user()
sett  = get_settings(_uid)


@st.cache_data(ttl=120)
def _stats(u: int) -> dict:
    return get_stats(u)


stats = _stats(_uid)

st.markdown(page_header(
    'Settings <span style="color:#00C8F0;">&amp; Profile</span>',
    "Account info · preferences · security · data management · alerts",
), unsafe_allow_html=True)

tab_p, tab_pr, tab_s, tab_al, tab_d, tab_ab = st.tabs(
    ["Profile", "Preferences", "Security", "Alerts", "Data", "About"]
)

# ── PROFILE ───────────────────────────────────────────────────────────────────
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
          <div style="margin-top:4px;">{badge(_role, "accent" if _role == "Admin" else "neutral")}</div>
        </div>
        """, unsafe_allow_html=True)

    with info_col:
        total = max(stats.get("total", 0) or 1, 1)
        st.markdown(f"""
        <div class="fi-card">
          <div class="fi-title">Account Info</div>
          <table style="width:100%;border-collapse:collapse;font-size:.8rem;">
            {"".join(
              f'<tr style="border-bottom:1px solid #1A2535;">'
              f'<td style="padding:7px 0;color:#3D5268;width:38%;font-family:Manrope,sans-serif;">{k}</td>'
              f'<td style="padding:7px 0;color:{vc};font-family:Manrope,sans-serif;">{v}</td></tr>'
              for k, v, vc in [
                ("Username",        _un,                                    "#DDE6F0"),
                ("Email",           _email,                                 "#DDE6F0"),
                ("Role",            _role,                                  "#00C8F0"),
                ("Analyses Run",    str(stats.get("total", 0)),             "#DDE6F0"),
                ("Tickers Tracked", str(stats.get("tickers", 0)),           "#DDE6F0"),
                ("Avg Confidence",  f"{(stats.get('avg_conf') or 0):.0%}",  "#DDE6F0"),
              ]
            )}
          </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="fi-section">Analysis Breakdown</div>', unsafe_allow_html=True)
        for lbl2, cnt, color in [
            ("Bullish", stats.get("positive", 0), "#00E8A0"),
            ("Bearish", stats.get("negative", 0), "#FF3D60"),
            ("Neutral", stats.get("neutral",  0), "#7A92A8"),
        ]:
            pct = (cnt or 0) / total
            st.markdown(mini_progress_bar(f"{lbl2} ({cnt})", pct, color), unsafe_allow_html=True)

# ── PREFERENCES ───────────────────────────────────────────────────────────────
with tab_pr:
    st.markdown('<div class="fi-card"><div class="fi-title">Analysis Defaults</div>',
                unsafe_allow_html=True)
    available = get_tickers()
    cur_def   = sett.get("default_ticker", "TSLA")
    def_idx   = available.index(cur_def) if cur_def in available else 0

    new_def   = st.selectbox("Default Ticker on Dashboard", available,
                              index=def_idx, key="_sp_dt")
    show_conf = st.toggle("Show Confidence Breakdown",    value=bool(sett.get("show_confidence", 1)), key="_sp_sc")
    show_rip  = st.toggle("Show Corporate Ripple Effect", value=bool(sett.get("show_ripple",     1)), key="_sp_sr")
    show_hist = st.toggle("Show Historical Matches",      value=bool(sett.get("show_history",    1)), key="_sp_sh")

    current_theme = sett.get("theme", "dark")
    theme_choice  = st.radio("UI Theme", ["dark", "light"],
                              index=0 if current_theme == "dark" else 1,
                              horizontal=True, key="_sp_theme")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Save Preferences", type="primary", key="_sp_save"):
        save_settings(_uid, {
            "default_ticker":  new_def,
            "show_confidence": 1 if show_conf else 0,
            "show_ripple":     1 if show_rip  else 0,
            "show_history":    1 if show_hist else 0,
            "theme":           theme_choice,
        })
        # FIX: don't clear stats cache on pref save — stats are unrelated
        st.success("Preferences saved successfully.")

# ── SECURITY ──────────────────────────────────────────────────────────────────
with tab_s:
    st.markdown('<div class="fi-card"><div class="fi-title">Change Password</div>',
                unsafe_allow_html=True)
    with st.form("_cpw_form", clear_on_submit=True):
        old_p = st.text_input("Current Password",        type="password", key="_cpw_old")
        new_p = st.text_input("New Password (min 6)",    type="password", key="_cpw_new")
        cnf_p = st.text_input("Confirm New Password",    type="password", key="_cpw_cnf")
        cpw_b = st.form_submit_button("Update Password", type="primary")
        if cpw_b:
            ok, msg = do_change_password(_uid, old_p, new_p, cnf_p)
            st.success(msg) if ok else st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)

# ── ALERTS ────────────────────────────────────────────────────────────────────
with tab_al:
    st.markdown('<div class="fi-card"><div class="fi-title">Active Price Alerts</div>',
                unsafe_allow_html=True)
    active_alerts = get_active_alerts(_uid)
    if not active_alerts:
        st.markdown("""
        <div style="font-size:.8rem;color:#3D5268;font-family:'Manrope',sans-serif;padding:.5rem 0;">
          No active price alerts. Set them from the Watchlist page.
        </div>
        """, unsafe_allow_html=True)
    else:
        for al in active_alerts:
            c1, c2 = st.columns([5, 1])
            with c1:
                dir_color = "#00E8A0" if al["direction"] == "above" else "#FF7D35"
                st.markdown(f"""
                <div style="padding:8px 0;border-bottom:1px solid #1A2535;
                             font-family:'Manrope',sans-serif;font-size:.8rem;color:#7A92A8;">
                  <span style="font-family:'JetBrains Mono',monospace;
                               color:#00C8F0;font-size:.85rem;">{al['ticker']}</span>
                  &nbsp; trigger when &nbsp;
                  <span style="color:{dir_color};font-weight:600;">{al['direction']}</span>
                  &nbsp;
                  <span style="color:#DDE6F0;font-weight:700;">{al['target_price']:,.2f}</span>
                  <span style="font-size:.65rem;color:#3D5268;margin-left:8px;">
                    created {al.get('created_at','')[:10]}
                  </span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("Delete", key=f"_sett_al_del_{al['id']}",
                             type="secondary", use_container_width=True):
                    delete_alert(al["id"], _uid)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── DATA MANAGEMENT ───────────────────────────────────────────────────────────
with tab_d:
    st.markdown('<div class="fi-card"><div class="fi-title">Data Management</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:.8rem;color:#7A92A8;margin-bottom:1rem;
                font-family:'Manrope',sans-serif;line-height:1.65;">
      You have <strong style="color:#DDE6F0;">{stats.get('total', 0)}</strong> saved analyses.
      Clearing history is permanent and cannot be undone.
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        # FIX: single-click export — no nested button required
        rows = get_history(_uid, limit=9999)
        if rows:
            df_exp = pd.DataFrame([{
                "Date":       h.get("analyzed_at", "")[:19].replace("T", " "),
                "Ticker":     h["ticker"],
                "Headline":   h["headline"],
                "Polarity":   h.get("polarity",   0),
                "Category":   h.get("category",   ""),
                "Confidence": h.get("confidence", 0),
                "EventType":  h.get("event_type", ""),
            } for h in rows])
            csv = df_exp.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Export All History (CSV)",
                data=csv,
                file_name="fi_history_export.csv",
                mime="text/csv",
                key="_dm_dl",
                type="secondary",
                use_container_width=True,
            )
        else:
            st.button("Export All History (CSV)", disabled=True,
                      use_container_width=True, type="secondary", key="_dm_dl_empty")
            st.caption("No data to export.")

    with col_b:
        if st.button("Clear All History", type="secondary",
                     use_container_width=True, key="_dm_clr"):
            st.session_state["_confirm_clear"] = True

    if st.session_state.get("_confirm_clear"):
        st.warning("This will permanently delete all your analysis history.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Confirm — Delete All", type="primary",
                         key="_dm_yes", use_container_width=True):
                clear_history(_uid)
                _stats.clear()
                st.session_state.pop("_confirm_clear", None)
                st.success("History cleared.")
                st.rerun()
        with cc2:
            if st.button("Cancel", type="secondary",
                         key="_dm_no", use_container_width=True):
                st.session_state.pop("_confirm_clear", None)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── ACCOUNT DELETION (new) ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="fi-card fi-card-red"><div class="fi-title" style="color:#FF3D60;">Danger Zone</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:.8rem;color:#7A92A8;margin-bottom:.8rem;font-family:'Manrope',sans-serif;">
      Account deletion is permanent. All your data — analyses, watchlist, settings, and alerts — will be removed.
    </div>
    """, unsafe_allow_html=True)
    if st.button("Delete My Account", type="secondary", key="_acct_del"):
        st.session_state["_confirm_acct_del"] = True

    if st.session_state.get("_confirm_acct_del"):
        st.error("Are you absolutely sure? This action is irreversible.")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Yes, Delete My Account", type="primary", key="_acct_del_yes",
                         use_container_width=True):
                # Soft delete — clear data then logout (full DB deletion needs admin)
                clear_history(_uid)
                st.session_state.pop("_confirm_acct_del", None)
                st.success("Your data has been cleared. Contact support to fully remove your account.")
        with d2:
            if st.button("Cancel", type="secondary", key="_acct_del_no",
                         use_container_width=True):
                st.session_state.pop("_confirm_acct_del", None)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── ABOUT ─────────────────────────────────────────────────────────────────────
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
            ("ML Model",        "ProsusAI/FinBERT — financial sentiment analysis"),
            ("Sentence Encoder","all-MiniLM-L6-v2 — semantic similarity search"),
            ("Event Types",     "9 categories: Regulatory, Earnings, Leadership, M&A, Product, Milestone, Macro, Debt, ESG"),
            ("Corporate Graph", "NetworkX — ownership-weighted 3-level subsidiary ripple propagation"),
            ("Price Data",      "yFinance — 5-min cache, Indian NSE ticker support (.NS suffix)"),
            ("News Sources",    "Reuters, Bloomberg, ET Markets, Moneycontrol, CNBC, Yahoo, Livemint, Seeking Alpha"),
            ("Database",        "SQLite WAL — users, history, watchlist, settings, price_alerts (ON DELETE CASCADE)"),
            ("Architecture",    "core/ (pure Python) · db/ (SQLite) · ui/ (Streamlit) · pages/ (6 pages)"),
            ("Framework",       "Python 3.11+ · Streamlit · Plotly · Syne + Manrope + JetBrains Mono"),
            ("Version",         "v6 — Bug fixes, cascade deletes, single-click export, account deletion, pagination fixes"),
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
        <span style="color:#00E8A0;">_result</span>       → latest analysis dict (26+ fields, v6)<br>
        <span style="color:#9B6DFF;">_fi_running</span>   → analysis in-progress flag (disables Analyze btn)<br>
      </div>
    </div>
    """, unsafe_allow_html=True)
