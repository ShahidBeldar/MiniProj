"""
pages/3_Watchlist.py — Portfolio Watchlist with live prices + history chart.
FIX: Broken f-string in watchlist row notes display — was a SyntaxError.
FIX: Parallel price fetching via ThreadPoolExecutor.
NEW: Price alert creation & toast notifications.
FIX: render_sidebar() called for consistent navigation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from ui.theme import inject_css
from ui.auth import require_login, uid
from ui.nav import render_sidebar
from ui.components import page_header, badge, sentiment_color, mini_progress_bar
from db.ops import (
    get_watchlist, add_watch, remove_watch, get_history,
    get_active_alerts, add_alert, mark_alert_triggered, delete_alert,
)
from core.stocks import (
    get_price, get_history as price_history,
    fmt_price, fmt_change, chg_color,
)
from core.graph import get_tickers

inject_css()
require_login()
render_sidebar("watchlist")

_uid = uid()

_TKR_NAME = {
    "TSLA":     "Tesla, Inc.",              "AAPL":     "Apple Inc.",
    "GOOGL":    "Alphabet Inc.",            "MSFT":     "Microsoft Corp.",
    "NVDA":     "NVIDIA Corp.",             "AMZN":     "Amazon.com Inc.",
    "RELIANCE": "Reliance Industries",      "TCS":      "Tata Consultancy Services",
    "INFY":     "Infosys Ltd.",             "WIPRO":    "Wipro Ltd.",
    "HDFCBANK": "HDFC Bank Ltd.",
}

st.markdown(page_header(
    'Portfolio <span style="color:#00C8F0;">Watchlist</span>',
    "Live prices · sentiment · day change · 90-day performance · price alerts",
), unsafe_allow_html=True)

# ── ADD TICKER ────────────────────────────────────────────────────────────────

with st.expander("Add Ticker to Watchlist", expanded=False):
    ca, cb, cc = st.columns([2, 3, 1])
    with ca:
        new_t = st.selectbox("Ticker", get_tickers(), key="_wl_t")
    with cb:
        new_n = st.text_input("Notes (optional)", placeholder="e.g. Long-term hold", key="_wl_n")
    with cc:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary", use_container_width=True, key="_wl_add"):
            if add_watch(_uid, new_t, _TKR_NAME.get(new_t, new_t), new_n):
                st.success(f"{new_t} added to watchlist.")
            else:
                st.info(f"{new_t} is already in your watchlist.")
            st.rerun()

wl = get_watchlist(_uid)

if not wl:
    st.markdown("""
    <div style="text-align:center;padding:3.5rem;color:#3D5268;">
      <div style="font-family:'Syne',sans-serif;color:#2D4060;margin-bottom:.4rem;">
        Your watchlist is empty</div>
      <div style="font-size:.76rem;font-family:'Manrope',sans-serif;">
        Use the expander above to add tickers.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

tickers  = [w["ticker"] for w in wl]
hist_all = get_history(_uid, limit=300)

# ── PARALLEL PRICE FETCH ──────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner="Fetching live prices…")
def _prices(tklist: tuple) -> dict:
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(get_price, t): t for t in tklist}
        result  = {}
        for f in as_completed(futures):
            t = futures[f]
            try:
                result[t] = f.result(timeout=8)
            except Exception:
                result[t] = {"ticker": t, "price": 0.0, "change": 0.0,
                              "chg_pct": 0.0, "currency": "$", "error": True,
                              "msg": "Price data unavailable"}
    return result

prices = _prices(tuple(tickers))

# ── PRICE ALERT CHECKS ────────────────────────────────────────────────────────

for alert in get_active_alerts(_uid):
    price_val = prices.get(alert["ticker"], {}).get("price", 0)
    if price_val and (
        (alert["direction"] == "above" and price_val >= alert["target_price"]) or
        (alert["direction"] == "below" and price_val <= alert["target_price"])
    ):
        st.toast(
            f"🔔 {alert['ticker']} hit target {alert['target_price']:,.2f}!",
            icon="🔔",
        )
        mark_alert_triggered(alert["id"])

# ── SUMMARY METRICS ───────────────────────────────────────────────────────────

gainers = sum(1 for t in tickers if prices[t].get("chg_pct", 0) > 0)
losers  = sum(1 for t in tickers if prices[t].get("chg_pct", 0) < 0)

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Positions", len(wl))
with m2: st.metric("Gainers",   gainers)
with m3: st.metric("Losers",    losers)
with m4: st.metric("Flat",      len(wl) - gainers - losers)

st.markdown("<br>", unsafe_allow_html=True)

# ── WATCHLIST ROWS ────────────────────────────────────────────────────────────

for item in wl:
    t     = item["ticker"]
    pd_   = prices.get(t, {})
    cc    = chg_color(pd_)
    pstr  = fmt_price(pd_)
    cstr  = fmt_change(pd_)
    chgp  = pd_.get("chg_pct", 0)

    t_hist = [h for h in hist_all if h["ticker"] == t]
    last_c = t_hist[0]["category"] if t_hist else None
    sc     = sentiment_color(last_c) if last_c else "#3D5268"
    sl     = (last_c or "No analyses yet").replace("_", " ").title()

    bw     = min(100, abs(chgp) * 10)
    bc     = "#00E8A0" if chgp >= 0 else "#FF3D60"
    arrow  = "▲" if chgp > 0 else ("▼" if chgp < 0 else "—")

    # Notes text — FIX: was a truncated broken f-string in original
    notes_text = item.get("notes", "") or ""
    notes_html = (
        f'<div style="font-size:.65rem;color:#7A92A8;margin-top:4px;'
        f'font-family:Manrope,sans-serif;">{notes_text}</div>'
        if notes_text else ""
    )

    ci, cp, cs, ca2 = st.columns([3, 2, 2, 1])

    with ci:
        st.markdown(f"""
        <div style="padding:12px 0;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;
                      font-size:.98rem;color:#DDE6F0;">{t}</div>
          <div style="font-size:.68rem;color:#3D5268;margin-top:2px;
                      font-family:'Manrope',sans-serif;">{_TKR_NAME.get(t, t)}</div>
          {notes_html}
        </div>
        """, unsafe_allow_html=True)

    with cp:
        st.markdown(f"""
        <div style="padding:12px 0;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;
                      font-size:.98rem;color:#DDE6F0;">{pstr}</div>
          <div style="font-size:.76rem;color:{cc};margin-top:3px;
                      font-family:'Manrope',sans-serif;">{arrow} {cstr}</div>
          <div style="height:3px;background:#0F1520;border-radius:2px;
                      overflow:hidden;margin-top:6px;">
            <div style="height:100%;width:{bw}%;background:{bc};border-radius:2px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with cs:
        st.markdown(f"""
        <div style="padding:12px 0;">
          <div style="font-size:.62rem;color:#3D5268;margin-bottom:3px;
                      font-family:'Manrope',sans-serif;letter-spacing:.08em;
                      text-transform:uppercase;">Last Analysis</div>
          <div style="font-family:'Syne',sans-serif;font-weight:600;
                      font-size:.82rem;color:{sc};">{sl}</div>
          <div style="font-size:.64rem;color:#3D5268;margin-top:2px;
                      font-family:'Manrope',sans-serif;">
            {len(t_hist)} {"analyses" if len(t_hist) != 1 else "analysis"}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with ca2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Analyze", key=f"_wl_an_{t}", use_container_width=True):
            st.session_state["_pending_t"]  = t
            st.session_state["_pending_hl"] = ""
            st.switch_page("pages/1_Dashboard.py")

        # Confirm before removing
        if st.button("Remove", key=f"_wl_rm_{t}", type="secondary", use_container_width=True):
            st.session_state[f"_wl_confirm_rm_{t}"] = True

        if st.session_state.get(f"_wl_confirm_rm_{t}"):
            st.warning(f"Remove {t}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes", key=f"_wl_rm_yes_{t}", type="primary",
                             use_container_width=True):
                    remove_watch(_uid, t)
                    st.session_state.pop(f"_wl_confirm_rm_{t}", None)
                    st.rerun()
            with c2:
                if st.button("No", key=f"_wl_rm_no_{t}", type="secondary",
                             use_container_width=True):
                    st.session_state.pop(f"_wl_confirm_rm_{t}", None)
                    st.rerun()

    st.markdown('<div class="fi-divider"></div>', unsafe_allow_html=True)

# ── PRICE ALERTS ─────────────────────────────────────────────────────────────

with st.expander("Price Alerts", expanded=False):
    ac1, ac2, ac3, ac4 = st.columns([2, 2, 2, 1])
    with ac1:
        alert_t = st.selectbox("Ticker", tickers, key="_al_t")
    with ac2:
        alert_price = st.number_input("Target Price", min_value=0.01,
                                       value=float(prices.get(alert_t, {}).get("price", 100) or 100),
                                       step=1.0, key="_al_p")
    with ac3:
        alert_dir = st.radio("Trigger when price goes", ["above", "below"],
                              horizontal=True, key="_al_d")
    with ac4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Set Alert", type="primary", use_container_width=True, key="_al_add"):
            if add_alert(_uid, alert_t, alert_price, alert_dir):
                st.success(f"Alert set: {alert_t} {alert_dir} {alert_price:,.2f}")
            else:
                st.error("Failed to set alert.")

    active_alerts = get_active_alerts(_uid)
    if active_alerts:
        st.markdown('<div class="fi-section">Active Alerts</div>', unsafe_allow_html=True)
        for al in active_alerts:
            alc1, alc2 = st.columns([5, 1])
            with alc1:
                st.markdown(f"""
                <div style="padding:6px 0;font-family:'Manrope',sans-serif;font-size:.8rem;
                             color:#7A92A8;">
                  <span style="font-family:'JetBrains Mono',monospace;color:#00C8F0;">{al['ticker']}</span>
                  &nbsp;→&nbsp; {al['direction']} &nbsp;
                  <strong style="color:#DDE6F0;">{al['target_price']:,.2f}</strong>
                  <span style="font-size:.65rem;color:#3D5268;margin-left:8px;">
                    set {al.get('created_at','')[:10]}
                  </span>
                </div>
                """, unsafe_allow_html=True)
            with alc2:
                if st.button("Delete", key=f"_al_del_{al['id']}",
                             type="secondary", use_container_width=True):
                    delete_alert(al["id"], _uid)
                    st.rerun()

# ── TODAY'S PERFORMANCE CHART ─────────────────────────────────────────────────

chg_map = {t: prices[t].get("chg_pct", 0) for t in tickers if not prices[t].get("error")}
if chg_map:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="fi-section">Today\'s Performance Overview</div>',
                unsafe_allow_html=True)
    sorted_map = dict(sorted(chg_map.items(), key=lambda x: x[1]))
    colors = ["#00E8A0" if v >= 0 else "#FF3D60" for v in sorted_map.values()]
    fig = go.Figure(go.Bar(
        x=list(sorted_map.values()),
        y=list(sorted_map.keys()),
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in sorted_map.values()],
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
        font=dict(color="#7A92A8", size=10, family="Manrope"),
        xaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A", title="Day Change %"),
        yaxis=dict(gridcolor="#1A2535"),
        margin=dict(l=10, r=65, t=10, b=10),
        height=max(180, len(sorted_map) * 42),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── 90-DAY NORMALISED CHART ───────────────────────────────────────────────────

if len(tickers) <= 6:
    st.markdown('<div class="fi-section">90-Day Price History (Normalised)</div>',
                unsafe_allow_html=True)

    @st.cache_data(ttl=900, show_spinner=False)
    def _hist(t: str):
        return price_history(t, days=90)

    fig3 = go.Figure()
    for t in tickers:
        dfh = _hist(t)
        if dfh.empty:
            continue
        close = dfh.get("Close") if "Close" in dfh.columns else None
        if close is None or close.empty:
            continue
        norm = close / close.iloc[0] * 100
        fig3.add_trace(go.Scatter(
            x=dfh.index, y=norm,
            mode="lines", name=t,
            line=dict(width=1.5),
            hovertemplate=f"<b>{t}</b>: %{{y:.1f}}<extra></extra>",
        ))

    if fig3.data:
        fig3.update_layout(
            paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
            font=dict(color="#7A92A8", size=10, family="Manrope"),
            xaxis=dict(gridcolor="#1A2535"),
            yaxis=dict(gridcolor="#1A2535", title="Indexed (base 100)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
            margin=dict(l=10, r=10, t=10, b=10),
            height=270,
        )
        st.plotly_chart(fig3, use_container_width=True)
