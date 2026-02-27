"""
pages/history.py — Analysis History.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.auth   import require_login, current_user_id
from utils.styles import inject_styles, badge_html, sentiment_color, sentiment_badge_kind
from utils.db     import get_user_history, get_user_stats, delete_history_item, clear_user_history

st.set_page_config(page_title="History · Finance Impact", layout="wide")
st.session_state["_current_page"] = "history"
require_login()
inject_styles()

uid = current_user_id()

st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1>Analysis <span style="color:#00C8F0;">History</span></h1>
        <p style="color:#3D5268;font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;">
            All past headline analyses with full results
        </p>
    </div>
""", unsafe_allow_html=True)

stats = get_user_stats(uid)
s1, s2, s3, s4, s5 = st.columns(5)
with s1: st.metric("Total Analyses",   stats.get("total", 0))
with s2: st.metric("Positive Signals", stats.get("positive", 0))
with s3: st.metric("Negative Signals", stats.get("negative", 0))
with s4: st.metric("Neutral",          stats.get("neutral", 0))
with s5:
    conf = stats.get("avg_confidence") or 0
    st.metric("Avg Confidence", f"{conf:.0%}" if conf else "—")

st.markdown("<br>", unsafe_allow_html=True)

history = get_user_history(uid, limit=100)

if not history:
    st.markdown("""
        <div style="text-align:center;padding:3rem;color:#3D5268;">
            <div style="font-family:'Syne',sans-serif;color:#7A92A8;margin-bottom:0.5rem;">
                No analysis history yet
            </div>
            <div style="font-size:0.8rem;">Run your first analysis on the Dashboard.</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

cf1, cf2, cf3, cf4 = st.columns([2, 2, 2, 1])
with cf1:
    t_opts = ["All"] + sorted(set(h["ticker"] for h in history))
    tf = st.selectbox("Ticker", t_opts, key="hist_tf")
with cf2:
    c_opts = ["All", "STRONG_POSITIVE", "POSITIVE", "NEUTRAL", "NEGATIVE", "STRONG_NEGATIVE"]
    cf = st.selectbox("Sentiment", c_opts, key="hist_cf")
with cf3:
    e_opts = ["All"] + sorted(set(h.get("event_type","General") or "General" for h in history))
    ef = st.selectbox("Event Type", e_opts, key="hist_ef")
with cf4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear All", type="secondary", use_container_width=True, key="clr_hist"):
        clear_user_history(uid)
        st.rerun()

filtered = history
if tf != "All": filtered = [h for h in filtered if h["ticker"] == tf]
if cf != "All": filtered = [h for h in filtered if h["category"] == cf]
if ef != "All": filtered = [h for h in filtered if h.get("event_type","General") == ef]

st.markdown(f"""
    <div style="font-size:0.72rem;color:#3D5268;margin-bottom:1rem;">
        Showing {len(filtered)} of {len(history)} analyses
    </div>
""", unsafe_allow_html=True)

if len(filtered) >= 3:
    df_h = pd.DataFrame(filtered)
    df_h["analyzed_at"] = pd.to_datetime(df_h["analyzed_at"])
    df_h = df_h.sort_values("analyzed_at")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_h["analyzed_at"], y=df_h["polarity"],
        mode="lines+markers",
        line=dict(color="#00C8F0", width=2),
        marker=dict(
            size=8,
            color=["#00E8A0" if p > 0.2 else "#FF3D60" if p < -0.2 else "#7A92A8"
                   for p in df_h["polarity"]],
        ),
        hovertemplate="<b>%{text}</b><br>Polarity: %{y:.2f}<extra></extra>",
        text=df_h["ticker"],
    ))
    fig.add_hline(y=0, line_color="#22334A", line_dash="dash")
    fig.update_layout(
        paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
        font=dict(color="#7A92A8", size=11),
        xaxis=dict(gridcolor="#1A2535", title="Date"),
        yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
                   title="Polarity", range=[-1.1, 1.1]),
        margin=dict(l=10, r=10, t=20, b=20),
        height=220, showlegend=False,
        title=dict(text="Sentiment Timeline", font=dict(color="#DDE6F0", size=13)),
    )
    st.plotly_chart(fig, use_container_width=True)

for item in filtered:
    pol  = item.get("polarity", 0) or 0
    cat  = item.get("category", "NEUTRAL") or "NEUTRAL"
    conf = item.get("confidence", 0) or 0
    evt  = item.get("event_type", "General") or "General"
    sc   = sentiment_color(cat)
    sk   = sentiment_badge_kind(cat)
    date = (item.get("analyzed_at") or "")[:16].replace("T", " ")

    cm, cme, ca2 = st.columns([4, 2, 1])
    with cm:
        st.markdown(f"""
            <div style="padding:10px 0;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    {badge_html(item['ticker'], 'accent')}
                    {badge_html(cat.replace('_',' ').title(), sk)}
                    {badge_html(evt, 'neutral')}
                    {'<span style="font-size:0.68rem;color:#FF7D35;">Rumour</span>' if item.get("is_rumour") else ""}
                </div>
                <div style="font-size:0.85rem;color:#DDE6F0;line-height:1.5;">
                    {item['headline']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cme:
        st.markdown(f"""
            <div style="padding:10px 0;text-align:right;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:1rem;color:{sc};">{pol:+.2f}</div>
                <div style="font-size:0.68rem;color:#3D5268;">Conf {conf:.0%}</div>
                <div style="font-size:0.68rem;color:#3D5268;margin-top:2px;">{date}</div>
            </div>
        """, unsafe_allow_html=True)
    with ca2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Re-analyze", key=f"re_{item['id']}", use_container_width=True):
            st.session_state["dash_ticker"]   = item["ticker"]
            st.session_state["dash_headline"] = item["headline"]
            st.switch_page("pages/dashboard.py")
        if st.button("Delete", key=f"del_{item['id']}", type="secondary", use_container_width=True):
            delete_history_item(item["id"], uid)
            st.rerun()

    st.markdown('<div class="fi-divider"></div>', unsafe_allow_html=True)
