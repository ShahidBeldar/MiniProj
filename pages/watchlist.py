"""
pages/watchlist.py — Portfolio Watchlist.
"""

import streamlit as st
import plotly.graph_objects as go

from utils.auth       import require_login, current_user_id
from utils.styles     import inject_styles, badge_html, sentiment_color
from utils.db         import get_watchlist, add_to_watchlist, remove_from_watchlist, get_user_history
from utils.stock_data import get_current_price, format_price, format_change, change_color
from utils.corporate_graph import get_available_tickers

st.set_page_config(page_title="Watchlist · Finance Impact", layout="wide")
st.session_state["_current_page"] = "watchlist"
require_login()
inject_styles()

uid = current_user_id()

TICKER_NAMES = {
    "TSLA": "Tesla, Inc.",       "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",    "MSFT": "Microsoft Corp.",
    "NVDA": "NVIDIA Corp.",      "AMZN": "Amazon.com Inc.",
    "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services",
    "INFY": "Infosys Ltd.",      "WIPRO": "Wipro Ltd.",
    "HDFCBANK": "HDFC Bank Ltd.",
}

st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1>Portfolio <span style="color:#00C8F0;">Watchlist</span></h1>
        <p style="color:#3D5268;font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;">
            Track live prices and recent sentiment for your portfolio
        </p>
    </div>
""", unsafe_allow_html=True)

with st.expander("Add New Ticker", expanded=False):
    ca, cb, cc = st.columns([2, 3, 1])
    with ca:
        new_t = st.selectbox("Ticker", get_available_tickers(), key="wl_new_t")
    with cb:
        new_n = st.text_input("Notes (optional)", placeholder="e.g. Long-term hold", key="wl_new_n")
    with cc:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary", use_container_width=True, key="wl_add"):
            add_to_watchlist(uid, new_t, TICKER_NAMES.get(new_t, new_t), new_n)
            st.success(f"{new_t} added.")
            st.rerun()

watchlist = get_watchlist(uid)

if not watchlist:
    st.markdown("""
        <div style="text-align:center;padding:3rem;color:#3D5268;">
            <div style="font-family:'Syne',sans-serif;color:#7A92A8;margin-bottom:0.5rem;">
                Your watchlist is empty
            </div>
            <div style="font-size:0.8rem;">
                Add tickers above or use the Add to Watchlist button on the Dashboard.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

tickers = [w["ticker"] for w in watchlist]
history = get_user_history(uid, limit=200)

price_cache = {}
with st.spinner("Fetching live prices..."):
    for t in tickers:
        price_cache[t] = get_current_price(t)

gainers = sum(1 for t in tickers if price_cache.get(t, {}).get("chg_pct", 0) > 0)
losers  = sum(1 for t in tickers if price_cache.get(t, {}).get("chg_pct", 0) < 0)

s1, s2, s3, s4 = st.columns(4)
with s1: st.metric("Positions", len(watchlist))
with s2: st.metric("Gainers",   gainers)
with s3: st.metric("Losers",    losers)
with s4: st.metric("Neutral",   len(watchlist) - gainers - losers)

st.markdown("<br>", unsafe_allow_html=True)

for item in watchlist:
    t        = item["ticker"]
    pdata    = price_cache.get(t, {})
    chg_c    = change_color(pdata)
    price    = format_price(pdata)
    chg      = format_change(pdata)
    chg_pct  = pdata.get("chg_pct", 0)
    t_hist   = [h for h in history if h["ticker"] == t]
    last_cat = t_hist[0]["category"] if t_hist else None
    sc       = sentiment_color(last_cat) if last_cat else "#3D5268"
    s_label  = last_cat.replace("_", " ").title() if last_cat else "No data"
    bar_w    = min(100, abs(chg_pct) * 10)
    bar_c    = "#00E8A0" if chg_pct >= 0 else "#FF3D60"
    arrow    = "+" if chg_pct > 0 else "-" if chg_pct < 0 else "="

    ci, cp, cs, ca = st.columns([3, 2, 2, 1])
    with ci:
        st.markdown(f"""
            <div style="padding:12px 0;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:1rem;color:#DDE6F0;">{t}</div>
                <div style="font-size:0.72rem;color:#3D5268;">{TICKER_NAMES.get(t, t)}</div>
                {f'<div style="font-size:0.68rem;color:#7A92A8;margin-top:3px;">{item.get("notes","")}</div>' if item.get("notes") else ""}
            </div>
        """, unsafe_allow_html=True)
    with cp:
        st.markdown(f"""
            <div style="padding:12px 0;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:1rem;color:#DDE6F0;">{price}</div>
                <div style="font-size:0.78rem;color:{chg_c};margin-top:2px;">{arrow} {chg}</div>
                <div style="height:3px;background:#0F1520;border-radius:2px;
                            overflow:hidden;margin-top:6px;">
                    <div style="height:100%;width:{bar_w}%;background:{bar_c};border-radius:2px;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cs:
        st.markdown(f"""
            <div style="padding:12px 0;">
                <div style="font-size:0.72rem;color:#3D5268;margin-bottom:4px;">Last Analysis</div>
                <div style="font-family:'Syne',sans-serif;font-weight:600;
                            font-size:0.82rem;color:{sc};">{s_label}</div>
                <div style="font-size:0.68rem;color:#3D5268;">
                    {f"{len(t_hist)} analyses" if t_hist else "No analyses yet"}
                </div>
            </div>
        """, unsafe_allow_html=True)
    with ca:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Analyze", key=f"an_{t}", use_container_width=True):
            st.session_state["dash_ticker"] = t
            st.switch_page("pages/dashboard.py")
        if st.button("Remove", key=f"rm_{t}", type="secondary", use_container_width=True):
            remove_from_watchlist(uid, t)
            st.rerun()

    st.markdown('<div class="fi-divider"></div>', unsafe_allow_html=True)

if tickers:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Performance Overview</div>', unsafe_allow_html=True)
    chg_data = {t: price_cache[t].get("chg_pct", 0)
                for t in tickers if not price_cache.get(t, {}).get("error")}
    if chg_data:
        colors = ["#00E8A0" if v >= 0 else "#FF3D60" for v in chg_data.values()]
        fig = go.Figure(go.Bar(
            x=list(chg_data.keys()),
            y=list(chg_data.values()),
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in chg_data.values()],
            textposition="outside",
        ))
        fig.update_layout(
            paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
            font=dict(color="#7A92A8", size=11),
            xaxis=dict(gridcolor="#1A2535"),
            yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A", title="Change %"),
            margin=dict(l=10, r=10, t=20, b=20),
            height=280, showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
