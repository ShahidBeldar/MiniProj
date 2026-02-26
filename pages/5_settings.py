"""
pages/5_settings.py — User Settings & Profile.
"""

import streamlit as st

from utils.auth import require_login, current_user, current_user_id, change_password
from utils.styles import inject_styles
from utils.database import get_user_settings, update_user_settings, get_user_stats
from utils.corporate_graph import get_available_tickers

st.set_page_config(page_title="Settings · Finance Impact",
                   page_icon="⚙️", layout="wide")
require_login()
inject_styles()

uid  = current_user_id()
user = current_user()
settings = get_user_settings(uid)
stats    = get_user_stats(uid)

st.markdown("""
    <h1>⚙️ Settings & <span style='color:#00C8F0;'>Profile</span></h1>
    <p style='color:#3D5268;font-size:0.78rem;letter-spacing:0.1em;
              text-transform:uppercase;margin-bottom:1.5rem;'>
        Manage your account, preferences, and analysis defaults
    </p>
""", unsafe_allow_html=True)

tab_profile, tab_prefs, tab_security, tab_about = st.tabs([
    "👤 Profile", "⚙️ Preferences", "🔒 Security", "ℹ️ About"
])

# ── PROFILE ───────────────────────────────────────────────────────────────────
with tab_profile:
    col_av, col_inf = st.columns([1, 3])
    with col_av:
        uname = user.get("username", "")
        st.markdown(f"""
            <div style='width:90px;height:90px;border-radius:50%;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        display:flex;align-items:center;justify-content:center;
                        font-size:2rem;font-weight:700;font-family:Syne,sans-serif;
                        margin:0 auto;border:3px solid #22334A;'>
                {uname[0].upper()}
            </div>
        """, unsafe_allow_html=True)

    with col_inf:
        st.markdown(f"""
            <div class="fi-card">
                <table style='width:100%;border-collapse:collapse;font-size:0.82rem;'>
                    <tr style='border-bottom:1px solid #1A2535;'>
                        <td style='padding:8px 0;color:#3D5268;width:35%;'>Username</td>
                        <td style='padding:8px 0;color:#DDE6F0;font-family:Syne,sans-serif;
                                   font-weight:600;'>{uname}</td>
                    </tr>
                    <tr style='border-bottom:1px solid #1A2535;'>
                        <td style='padding:8px 0;color:#3D5268;'>Email</td>
                        <td style='padding:8px 0;color:#DDE6F0;'>
                            {user.get('email', '') or '<span style="color:#3D5268;">Not set</span>'}
                        </td>
                    </tr>
                    <tr style='border-bottom:1px solid #1A2535;'>
                        <td style='padding:8px 0;color:#3D5268;'>Role</td>
                        <td style='padding:8px 0;color:#00C8F0;'>
                            {user.get('role', 'user').title()}
                        </td>
                    </tr>
                    <tr style='border-bottom:1px solid #1A2535;'>
                        <td style='padding:8px 0;color:#3D5268;'>Analyses Run</td>
                        <td style='padding:8px 0;color:#DDE6F0;'>
                            {stats.get('total', 0)}
                        </td>
                    </tr>
                    <tr>
                        <td style='padding:8px 0;color:#3D5268;'>Tickers Analyzed</td>
                        <td style='padding:8px 0;color:#DDE6F0;'>
                            {stats.get('unique_tickers', 0)}
                        </td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

    # Usage breakdown
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Analysis Breakdown</div>',
                unsafe_allow_html=True)

    total = stats.get("total", 0) or 1
    breakdown = [
        ("Positive", stats.get("positive", 0), "#00E8A0"),
        ("Negative", stats.get("negative", 0), "#FF3D60"),
        ("Neutral",  stats.get("neutral", 0),  "#7A92A8"),
    ]
    for label, count, color in breakdown:
        pct = count / total * 100
        st.markdown(f"""
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>
                <div style='font-size:0.78rem;color:#7A92A8;width:70px;'>{label}</div>
                <div style='flex:1;height:6px;background:#0F1520;border-radius:3px;overflow:hidden;'>
                    <div style='height:100%;width:{pct:.0f}%;background:{color};border-radius:3px;'></div>
                </div>
                <div style='font-family:Syne,sans-serif;font-size:0.78rem;
                            font-weight:600;color:{color};width:30px;text-align:right;'>
                    {count}
                </div>
            </div>
        """, unsafe_allow_html=True)


# ── PREFERENCES ───────────────────────────────────────────────────────────────
with tab_prefs:
    st.markdown('<div class="fi-card">', unsafe_allow_html=True)
    st.markdown('<div class="fi-card-title">Analysis Defaults</div>', unsafe_allow_html=True)

    available = get_available_tickers()
    cur_default = settings.get("default_ticker", "TSLA")
    default_idx = available.index(cur_default) if cur_default in available else 0

    new_default = st.selectbox(
        "Default Ticker",
        available,
        index=default_idx,
        key="pref_default_ticker",
    )

    show_conf   = st.toggle("Show Confidence Scores",   value=bool(settings.get("show_confidence", 1)))
    show_ripple = st.toggle("Show Corporate Ripple",    value=bool(settings.get("show_ripple", 1)))
    show_hist   = st.toggle("Show Historical Matches",  value=bool(settings.get("show_history", 1)))

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Save Preferences", type="primary", key="save_prefs"):
        update_user_settings(uid, {
            "default_ticker":  new_default,
            "show_confidence": 1 if show_conf else 0,
            "show_ripple":     1 if show_ripple else 0,
            "show_history":    1 if show_hist else 0,
        })
        st.success("Preferences saved!")


# ── SECURITY ──────────────────────────────────────────────────────────────────
with tab_security:
    st.markdown('<div class="fi-card">', unsafe_allow_html=True)
    st.markdown('<div class="fi-card-title">Change Password</div>', unsafe_allow_html=True)

    with st.form("change_pw_form", clear_on_submit=True):
        old_pw   = st.text_input("Current Password", type="password")
        new_pw   = st.text_input("New Password (min. 6 chars)", type="password")
        conf_pw  = st.text_input("Confirm New Password", type="password")
        pw_btn   = st.form_submit_button("Update Password", type="primary")

    if pw_btn:
        ok, msg = change_password(uid, old_pw, new_pw, conf_pw)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown('</div>', unsafe_allow_html=True)


# ── ABOUT ─────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
        <div class="fi-card">
            <div class="fi-card-title">Finance Impact — Platform Info</div>
            <table style='width:100%;border-collapse:collapse;font-size:0.82rem;'>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;width:40%;'>ML Model</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>ProsusAI/FinBERT</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Sentence Encoder</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>all-MiniLM-L6-v2</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Corporate Data</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>SEC EDGAR Exhibit 21 + MCA21 + curated hierarchy</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Price Data</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>yFinance (15-min delayed)</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>News Sources</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>Reuters, Bloomberg, ET Markets, Moneycontrol (RSS)</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Graph Engine</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>NetworkX — corporate ownership graph</td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#3D5268;'>Framework</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>Python · Streamlit · Plotly</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)
