"""
pages/3_watchlist.py — Portfolio Watchlist.
Add tickers, track live prices, see recent sentiment for each.
"""

import streamlit as st
import plotly.graph_objects as go

from utils.auth import require_login, current_user_id
from utils.styles import inject_styles, badge_html, sentiment_color
from utils.database import get_watchlist, add_to_watchlist, remove_from_watchlist, get_user_history
from utils.stock_data import get_current_price, format_price, format_change, change_color
from utils.corporate_graph import get_available_tickers

st.set_page_config(page_title="Watchlist · Finance Impact",
                   page_icon="📊", layout="wide")
require_login()
inject_styles()

uid = current_user_id()

TICKER_NAMES = {
    "TSLA": "Tesla, Inc.", "AAPL": "Apple Inc.", "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corp.", "NVDA": "NVIDIA Corp.", "AMZN": "Amazon.com",
    "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services",
    "INFY": "Infosys Ltd.", "WIPRO": "Wipro Ltd.", "HDFCBANK": "HDFC Bank Ltd.",
}

st.markdown("""
    <h1>📊 Portfolio <span style='color:#00C8F0;'>Watchlist</span></h1>
    <p style='color:#3D5268;font-size:0.78rem;letter-spacing:0.1em;
              text-transform:uppercase;margin-bottom:1.5rem;'>
        Track live prices and recent sentiment for your portfolio
    </p>
""", unsafe_allow_html=True)

# ── ADD TO WATCHLIST ──────────────────────────────────────────────────────────
with st.expander("➕ Add New Ticker", expanded=False):
    ca, cb, cc = st.columns([2, 3, 1])
    with ca:
        new_ticker = st.selectbox("Ticker", get_available_tickers(), key="wl_new_ticker")
    with cb:
        new_notes = st.text_input("Notes (optional)", placeholder="e.g. Long-term hold",
                                   key="wl_new_notes")
    with cc:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary", use_container_width=True, key="wl_add_btn"):
            cname = TICKER_NAMES.get(new_ticker, new_ticker)
            if add_to_watchlist(uid, new_ticker, cname, new_notes):
                st.success(f"Added {new_ticker} to watchlist!")
                st.rerun()
            else:
                st.info(f"{new_ticker} already in watchlist.")

# ── LOAD WATCHLIST ────────────────────────────────────────────────────────────
watchlist = get_watchlist(uid)

if not watchlist:
    st.markdown("""
        <div style='text-align:center;padding:3rem;color:#3D5268;'>
            <div style='font-size:2rem;opacity:0.3;margin-bottom:1rem;'>📊</div>
            <div style='font-family:Syne,sans-serif;color:#7A92A8;margin-bottom:0.5rem;'>
                Your watchlist is empty
            </div>
            <div style='font-size:0.8rem;'>
                Add tickers above or use the + Watchlist button on the Dashboard.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── FETCH PRICES ──────────────────────────────────────────────────────────────
tickers = [w["ticker"] for w in watchlist]
history = get_user_history(uid, limit=200)

price_cache = {}
with st.spinner("Fetching live prices…"):
    for t in tickers:
        price_cache[t] = get_current_price(t)

# ── SUMMARY ROW ───────────────────────────────────────────────────────────────
gainers = sum(1 for t in tickers if price_cache.get(t, {}).get("chg_pct", 0) > 0)
losers  = sum(1 for t in tickers if price_cache.get(t, {}).get("chg_pct", 0) < 0)

s1, s2, s3, s4 = st.columns(4)
with s1: st.metric("Positions", len(watchlist))
with s2: st.metric("Gainers",   gainers)
with s3: st.metric("Losers",    losers,  delta_color="inverse")
with s4: st.metric("Neutral",   len(watchlist) - gainers - losers)

st.markdown("<br>", unsafe_allow_html=True)

# ── WATCHLIST TABLE ───────────────────────────────────────────────────────────
for item in watchlist:
    t      = item["ticker"]
    pdata  = price_cache.get(t, {})
    chg_c  = change_color(pdata)
    price  = format_price(pdata)
    chg    = format_change(pdata)
    chg_pct = pdata.get("chg_pct", 0)

    # Latest sentiment from history
    ticker_hist = [h for h in history if h["ticker"] == t]
    last_sent   = ticker_hist[0]["category"] if ticker_hist else None
    sc          = sentiment_color(last_sent) if last_sent else "#3D5268"
    sent_label  = last_sent.replace("_", " ").title() if last_sent else "No data"

    # Price change bar fill
    bar_width = min(100, abs(chg_pct) * 10)
    bar_color = "#00E8A0" if chg_pct >= 0 else "#FF3D60"

    arrow = "▲" if chg_pct > 0 else "▼" if chg_pct < 0 else "—"

    col_info, col_price, col_sent, col_act = st.columns([3, 2, 2, 1])

    with col_info:
        st.markdown(f"""
            <div style='padding:12px 0;'>
                <div style='font-family:Syne,sans-serif;font-weight:700;
                            font-size:1rem;color:#DDE6F0;'>{t}</div>
                <div style='font-size:0.72rem;color:#3D5268;'>
                    {TICKER_NAMES.get(t, t)}
                </div>
                {f'<div style="font-size:0.68rem;color:#7A92A8;margin-top:3px;">{item.get("notes","")}</div>' if item.get("notes") else ""}
            </div>
        """, unsafe_allow_html=True)

    with col_price:
        st.markdown(f"""
            <div style='padding:12px 0;'>
                <div style='font-family:Syne,sans-serif;font-weight:700;
                            font-size:1rem;color:#DDE6F0;'>{price}</div>
                <div style='font-size:0.78rem;color:{chg_c};margin-top:2px;'>
                    {arrow} {chg}
                </div>
                <div style='height:3px;background:#0F1520;border-radius:2px;
                            overflow:hidden;margin-top:6px;'>
                    <div style='height:100%;width:{bar_width}%;
                                background:{bar_color};border-radius:2px;'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_sent:
        st.markdown(f"""
            <div style='padding:12px 0;'>
                <div style='font-size:0.72rem;color:#3D5268;margin-bottom:4px;'>
                    Last Analysis
                </div>
                <div style='font-family:Syne,sans-serif;font-weight:600;
                            font-size:0.82rem;color:{sc};'>{sent_label}</div>
                <div style='font-size:0.68rem;color:#3D5268;'>
                    {f"{len(ticker_hist)} analyses" if ticker_hist else "No analyses yet"}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_act:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡", key=f"analyze_{t}", help=f"Analyze {t}"):
            st.session_state["dash_ticker"] = t
            st.switch_page("pages/1_dashboard.py")
        if st.button("✕", key=f"remove_{t}", help=f"Remove {t}", type="secondary"):
            remove_from_watchlist(uid, t)
            st.rerun()

    st.markdown('<div class="fi-divider"></div>', unsafe_allow_html=True)

# ── PRICE CHART ───────────────────────────────────────────────────────────────
if tickers:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Performance Overview</div>',
                unsafe_allow_html=True)

    chg_data = {
        t: price_cache[t].get("chg_pct", 0)
        for t in tickers if not price_cache.get(t, {}).get("error")
    }

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
            yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
                       title="Change %"),
            margin=dict(l=10, r=10, t=20, b=20),
            height=280,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
