"""
pages/6_Market.py — Full Market Analysis page.

Tabs:
  1. Overview     — global indices ticker band + sparklines
  2. Chart        — candlestick OR line chart with MA / BB / Volume overlays
  3. Indicators   — RSI, MACD, ATR sub-panels
  4. Compare      — normalised multi-ticker line chart + correlation heatmap
  5. Stock Info   — company fundamentals card
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Market · Finance Impact",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.theme      import inject_css, CHART_THEME
from ui.auth       import require_login
from ui.nav        import render_sidebar
from ui.components import page_header, badge, stat_box, stat_row

from core.stocks import (
    get_price, get_index_prices, get_ohlcv_with_indicators,
    get_multi_ticker, get_ticker_info, fmt_price, fmt_change, chg_color,
    rsi_signal, MARKET_INDICES, PERIOD_OPTIONS, ALL_TICKERS,
)

inject_css()
require_login()
st.session_state["_page"] = "market"
render_sidebar("market")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def _indices():
    return get_index_prices()

@st.cache_data(ttl=300)
def _ohlcv(ticker: str, period: str):
    return get_ohlcv_with_indicators(ticker, period)

@st.cache_data(ttl=600)
def _info(ticker: str):
    return get_ticker_info(ticker)

@st.cache_data(ttl=300)
def _multi(tickers: tuple, period: str):
    return get_multi_ticker(list(tickers), period)

@st.cache_data(ttl=300)
def _price(ticker: str):
    return get_price(ticker)


def _ct(**overrides) -> dict:
    """Return CHART_THEME merged with optional overrides."""
    t = dict(CHART_THEME)
    t.update(overrides)
    return t


def _apply_theme(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    theme = _ct(height=height)
    if title:
        theme["title"] = dict(text=title, font=dict(size=12, color="#DDE6F0", family="Syne"))
    fig.update_layout(**theme)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(page_header(
    'Market <span style="color:#00C8F0;">Analysis</span>',
    "Live charts · Candlestick · Technical indicators · Multi-ticker comparison"
), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CONTROLS (in sidebar — always visible)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="margin-top:.5rem;padding:.7rem .8rem;background:#0F1520;'
        'border-radius:10px;border:1px solid #1A2535;margin-bottom:.8rem;">'
        '<div style="font-size:.6rem;font-weight:700;color:#3D5268;letter-spacing:.15em;'
        'text-transform:uppercase;margin-bottom:.5rem;">Chart Settings</div>',
        unsafe_allow_html=True,
    )
    ticker = st.selectbox("Ticker", ALL_TICKERS, key="_mkt_ticker")
    period = st.selectbox("Period", list(PERIOD_OPTIONS.keys()),
                          index=2, key="_mkt_period")   # default 1 Month
    chart_type = st.radio("Chart Type", ["Candlestick", "Line"],
                          horizontal=True, key="_mkt_ct")
    st.markdown("</div>", unsafe_allow_html=True)

    # Overlay toggles
    st.markdown(
        '<div style="padding:.7rem .8rem;background:#0F1520;border-radius:10px;'
        'border:1px solid #1A2535;">'
        '<div style="font-size:.6rem;font-weight:700;color:#3D5268;letter-spacing:.15em;'
        'text-transform:uppercase;margin-bottom:.5rem;">Overlays</div>',
        unsafe_allow_html=True,
    )
    show_ma    = st.toggle("Moving Averages (20/50/200)", value=True,  key="_mkt_ma")
    show_bb    = st.toggle("Bollinger Bands",             value=False, key="_mkt_bb")
    show_vwap  = st.toggle("VWAP",                        value=False, key="_mkt_vwap")
    show_vol   = st.toggle("Volume Bars",                 value=True,  key="_mkt_vol")
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs([
    "🌐 Overview", "📈 Chart", "📊 Indicators", "🔀 Compare", "🏢 Stock Info"
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW  (global index ticker band + sparklines)
# ════════════════════════════════════════════════════════════════════════════
with t1:
    st.markdown('<div class="fi-section">Global Indices — Live</div>', unsafe_allow_html=True)

    with st.spinner("Fetching index prices…"):
        idx_data = _indices()

    # --- Ticker band (2 rows of 5) ---
    idx_names = list(idx_data.keys())
    for row_start in range(0, len(idx_names), 5):
        cols = st.columns(5)
        for i, name in enumerate(idx_names[row_start: row_start + 5]):
            d = idx_data[name]
            if d.get("error"):
                with cols[i]:
                    st.markdown(
                        f'<div class="fi-card"><div class="stat-label">{name}</div>'
                        f'<div style="color:#3D5268;font-size:.8rem;">N/A</div></div>',
                        unsafe_allow_html=True,
                    )
                continue
            pct      = d["chg_pct"]
            color    = "#00E8A0" if pct >= 0 else "#FF3D60"
            arrow    = "▲" if pct >= 0 else "▼"
            border_c = "rgba(0,232,160,.20)" if pct >= 0 else "rgba(255,61,96,.20)"
            price_s  = f"{d['price']:,.2f}"
            with cols[i]:
                st.markdown(f"""
                    <div style="background:#111927;border:1px solid #1A2535;
                                border-top:2px solid {border_c};border-radius:12px;
                                padding:.85rem 1rem;margin-bottom:8px;">
                        <div style="font-size:.58rem;font-weight:700;color:#3D5268;
                                    letter-spacing:.14em;text-transform:uppercase;">{name}</div>
                        <div style="font-family:'Syne',sans-serif;font-weight:800;
                                    font-size:1.15rem;color:#DDE6F0;margin:.3rem 0 .15rem;">
                            {price_s}
                        </div>
                        <div style="font-size:.72rem;font-weight:600;color:{color};">
                            {arrow} {pct:+.2f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Sparkline grid — 3 key indices ---
    st.markdown('<div class="fi-section">Sparklines — 1 Month</div>', unsafe_allow_html=True)
    spark_tickers = [("S&P 500", "^GSPC"), ("NASDAQ", "^IXIC"), ("NIFTY 50", "^NSEI")]
    s1, s2, s3 = st.columns(3)
    for col, (name, sym) in zip([s1, s2, s3], spark_tickers):
        try:
            df_s = get_ohlcv_with_indicators(sym, "1 Month")
            if df_s.empty:
                raise ValueError("empty")
            closes  = df_s["Close"].tolist()
            dates   = [str(d)[:10] for d in df_s.index.tolist()]
            net_chg = ((closes[-1] - closes[0]) / closes[0]) * 100
            color   = "#00E8A0" if net_chg >= 0 else "#FF3D60"
            fill    = "rgba(0,232,160,.08)" if net_chg >= 0 else "rgba(255,61,96,.08)"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=closes, mode="lines",
                line=dict(color=color, width=1.5),
                fill="tozeroy", fillcolor=fill,
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
            ))
            fig.update_layout(
                **_ct(height=140, margin=dict(l=4, r=4, t=4, b=4)),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False, gridcolor="#1A2535"),
            )
            with col:
                st.markdown(f"""
                    <div style="font-size:.62rem;font-weight:700;color:#3D5268;
                                letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px;">
                        {name}
                    </div>
                    <div style="font-family:'Syne',sans-serif;font-size:.9rem;
                                font-weight:700;color:{color};">
                        {net_chg:+.2f}% (1M)
                    </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            with col:
                st.info(f"{name}: data unavailable")

    # --- Quick sector snapshot ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="fi-section">Quick Snapshot — Tracked Tickers</div>', unsafe_allow_html=True)
    snap_cols = st.columns(6)
    snap_tickers = ["TSLA", "AAPL", "NVDA", "RELIANCE", "TCS", "INFY"]
    for i, t in enumerate(snap_tickers):
        pd_ = _price(t)
        color = chg_color(pd_)
        with snap_cols[i]:
            st.markdown(f"""
                <div style="background:#0F1520;border:1px solid #1A2535;border-radius:10px;
                            padding:.7rem .85rem;text-align:center;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:.78rem;
                                font-weight:600;color:#00C8F0;">{t}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;
                                color:#DDE6F0;margin:.18rem 0 .1rem;">{fmt_price(pd_)}</div>
                    <div style="font-size:.7rem;color:{color};">{fmt_change(pd_)}</div>
                </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — CHART  (candlestick / line + overlays + volume)
# ════════════════════════════════════════════════════════════════════════════
with t2:
    with st.spinner(f"Loading {ticker} · {period}…"):
        df = _ohlcv(ticker, period)

    if df.empty:
        st.warning(f"No data available for **{ticker}** — check the ticker symbol or try a different period.")
        st.stop()

    price_d = _price(ticker)
    curr_price = fmt_price(price_d)
    curr_chg   = fmt_change(price_d)
    curr_color = chg_color(price_d)

    # Header metrics row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Current Price",  curr_price)
    with m2: st.metric("Day Change",     curr_chg)
    with m3: st.metric("Period High",    f"{df['High'].max():,.2f}" if "High" in df.columns else "—")
    with m4: st.metric("Period Low",     f"{df['Low'].min():,.2f}"  if "Low"  in df.columns else "—")
    with m5:
        rng_pct = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100) if len(df) > 1 else 0
        st.metric("Period Return", f"{rng_pct:+.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build main price chart ──────────────────────────────────────────────
    row_heights = [0.68, 0.32] if show_vol else [1.0]
    rows        = 2            if show_vol else 1
    specs_list  = [[{"secondary_y": False}]] * rows

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        specs=specs_list,
    )

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            name=ticker,
            increasing=dict(line=dict(color="#00E8A0"), fillcolor="rgba(0,232,160,.7)"),
            decreasing=dict(line=dict(color="#FF3D60"), fillcolor="rgba(255,61,96,.7)"),
            hovertext=None,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines", name=ticker,
            line=dict(color="#00C8F0", width=2),
            fill="tozeroy",
            fillcolor="rgba(0,200,240,.05)",
            hovertemplate=f"{ticker}: %{{y:,.2f}}<extra></extra>",
        ), row=1, col=1)

    # Moving averages
    if show_ma:
        for col_name, color, dash in [
            ("MA20",  "#FFD060", "solid"),
            ("MA50",  "#FF7D35", "dash"),
            ("MA200", "#9B6DFF", "dot"),
        ]:
            if col_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col_name],
                    mode="lines", name=col_name,
                    line=dict(color=color, width=1.2, dash=dash),
                    hovertemplate=f"{col_name}: %{{y:,.2f}}<extra></extra>",
                ), row=1, col=1)

    # Bollinger Bands
    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"], mode="lines",
            name="BB Upper", line=dict(color="rgba(155,109,255,.5)", width=1, dash="dot"),
            hovertemplate="BB Upper: %{y:,.2f}<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"], mode="lines",
            name="BB Lower", line=dict(color="rgba(155,109,255,.5)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(155,109,255,.04)",
            hovertemplate="BB Lower: %{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    # VWAP
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"], mode="lines",
            name="VWAP", line=dict(color="#FF7D35", width=1.2, dash="dashdot"),
            hovertemplate="VWAP: %{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    # Volume bars
    if show_vol and "Volume" in df.columns:
        vol_colors = []
        closes = df["Close"].tolist()
        opens  = df["Open"].tolist() if "Open" in df.columns else closes
        for i in range(len(closes)):
            vol_colors.append("#00E8A0" if closes[i] >= opens[i] else "#FF3D60")
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            marker_opacity=0.5,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ), row=2 if show_vol else 1, col=1)

    # Apply theme
    fig.update_layout(
        **_ct(height=560 if show_vol else 440),
        title=dict(
            text=f"{ticker} · {chart_type} · {period}",
            font=dict(size=12, color="#DDE6F0", family="Syne"),
        ),
        xaxis_rangeslider_visible=False,
        showlegend=True,
    )
    fig.update_yaxes(title_text="Price",  row=1, col=1,
                     title_font=dict(size=9, color="#3D5268"))
    if show_vol:
        fig.update_yaxes(title_text="Volume", row=2, col=1,
                         title_font=dict(size=9, color="#3D5268"))

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True,
                                                           "modeBarButtonsToRemove": ["autoScale2d"]})


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — INDICATORS  (RSI, MACD, ATR)
# ════════════════════════════════════════════════════════════════════════════
with t3:
    with st.spinner(f"Computing indicators for {ticker}…"):
        dfi = _ohlcv(ticker, period)

    if dfi.empty:
        st.warning("No data available.")
    else:
        # Current indicator values
        latest  = dfi.iloc[-1]
        rsi_val = float(latest.get("RSI", 50.0))
        rsi_lbl, rsi_clr = rsi_signal(rsi_val)
        macd_v  = float(latest.get("MACD", 0.0))
        sig_v   = float(latest.get("MACD_Signal", 0.0))
        hist_v  = float(latest.get("MACD_Hist", 0.0))
        atr_v   = float(latest.get("ATR", 0.0))
        close_v = float(latest.get("Close", 0.0))
        atr_pct = (atr_v / close_v * 100) if close_v else 0.0

        # Indicator summary cards
        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1:
            st.markdown(stat_box(
                "RSI (14)", f"{rsi_val:.1f}", rsi_lbl, rsi_clr,
            ), unsafe_allow_html=True)
        with ic2:
            mc = "#00E8A0" if macd_v >= 0 else "#FF3D60"
            st.markdown(stat_box(
                "MACD", f"{macd_v:+.4f}", f"Signal {sig_v:.4f}", mc,
            ), unsafe_allow_html=True)
        with ic3:
            hc = "#00E8A0" if hist_v >= 0 else "#FF3D60"
            st.markdown(stat_box(
                "MACD Histogram", f"{hist_v:+.4f}", "Momentum", hc,
            ), unsafe_allow_html=True)
        with ic4:
            st.markdown(stat_box(
                "ATR (14)", f"{atr_v:.4f}", f"Volatility {atr_pct:.2f}%", "#9B6DFF",
            ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── RSI Chart ──────────────────────────────────────────────────────
        if "RSI" in dfi.columns:
            fig_rsi = go.Figure()
            rsi_colors = []
            for v in dfi["RSI"].tolist():
                if v >= 70:   rsi_colors.append("#FF3D60")
                elif v <= 30: rsi_colors.append("#00E8A0")
                else:         rsi_colors.append("#7A92A8")

            fig_rsi.add_trace(go.Scatter(
                x=dfi.index, y=dfi["RSI"], mode="lines",
                name="RSI", line=dict(color="#00C8F0", width=1.8),
                hovertemplate="RSI: %{y:.1f}<extra></extra>",
            ))
            fig_rsi.add_hline(y=70, line=dict(color="#FF3D60", width=1, dash="dash"))
            fig_rsi.add_hline(y=30, line=dict(color="#00E8A0", width=1, dash="dash"))
            fig_rsi.add_hrect(y0=70, y1=100, fillcolor="rgba(255,61,96,.04)",  line_width=0)
            fig_rsi.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,232,160,.04)", line_width=0)
            fig_rsi.update_layout(
                **_ct(height=220),
                title=dict(text="RSI (14)", font=dict(size=11, color="#DDE6F0", family="Syne")),
                yaxis=dict(range=[0, 100], gridcolor="#1A2535"),
            )
            st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})

        # ── MACD Chart ─────────────────────────────────────────────────────
        if "MACD" in dfi.columns:
            fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                     row_heights=[0.6, 0.4], vertical_spacing=0.04)
            fig_macd.add_trace(go.Scatter(
                x=dfi.index, y=dfi["MACD"],
                mode="lines", name="MACD",
                line=dict(color="#00C8F0", width=1.6),
                hovertemplate="MACD: %{y:.4f}<extra></extra>",
            ), row=1, col=1)
            fig_macd.add_trace(go.Scatter(
                x=dfi.index, y=dfi["MACD_Signal"],
                mode="lines", name="Signal",
                line=dict(color="#FF7D35", width=1.3, dash="dash"),
                hovertemplate="Signal: %{y:.4f}<extra></extra>",
            ), row=1, col=1)

            # Histogram bars
            hist_vals = dfi["MACD_Hist"].tolist()
            hist_colors = ["#00E8A0" if v >= 0 else "#FF3D60" for v in hist_vals]
            fig_macd.add_trace(go.Bar(
                x=dfi.index, y=dfi["MACD_Hist"],
                name="Histogram",
                marker_color=hist_colors, marker_opacity=0.7,
                hovertemplate="Hist: %{y:.4f}<extra></extra>",
            ), row=2, col=1)

            fig_macd.update_layout(
                **_ct(height=340),
                title=dict(text="MACD (12, 26, 9)", font=dict(size=11, color="#DDE6F0", family="Syne")),
                showlegend=True,
            )
            st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})

        # ── ATR Chart ──────────────────────────────────────────────────────
        if "ATR" in dfi.columns:
            fig_atr = go.Figure()
            fig_atr.add_trace(go.Scatter(
                x=dfi.index, y=dfi["ATR"], mode="lines",
                name="ATR (14)", line=dict(color="#9B6DFF", width=1.6),
                fill="tozeroy", fillcolor="rgba(155,109,255,.06)",
                hovertemplate="ATR: %{y:.4f}<extra></extra>",
            ))
            fig_atr.update_layout(
                **_ct(height=200),
                title=dict(text="ATR (14) — Average True Range", font=dict(size=11, color="#DDE6F0", family="Syne")),
            )
            st.plotly_chart(fig_atr, use_container_width=True, config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPARE  (normalised multi-ticker + correlation)
# ════════════════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="fi-section">Multi-Ticker Comparison</div>', unsafe_allow_html=True)

    c_left, c_right = st.columns([3, 1])
    with c_right:
        cmp_period = st.selectbox("Period", list(PERIOD_OPTIONS.keys()),
                                  index=2, key="_cmp_period")
        base_100 = st.toggle("Normalise to 100", value=True, key="_cmp_norm")
        cmp_tickers = st.multiselect(
            "Tickers to compare",
            options=ALL_TICKERS,
            default=["TSLA", "AAPL", "NVDA"],
            max_selections=6,
            key="_cmp_tickers",
        )

    if not cmp_tickers:
        with c_left:
            st.info("Select at least one ticker from the panel →")
    else:
        with st.spinner("Fetching comparison data…"):
            cmp_data = _multi(tuple(sorted(cmp_tickers)), cmp_period)

        COLORS = ["#00C8F0", "#00E8A0", "#FF7D35", "#9B6DFF", "#FFD060", "#FF3D60"]

        with c_left:
            fig_cmp = go.Figure()
            for i, (t, df_t) in enumerate(cmp_data.items()):
                if df_t.empty:
                    continue
                y = df_t["Close"].tolist()
                if base_100 and y[0] != 0:
                    y = [v / y[0] * 100 for v in y]
                fig_cmp.add_trace(go.Scatter(
                    x=df_t.index.tolist(), y=y,
                    mode="lines", name=t,
                    line=dict(color=COLORS[i % len(COLORS)], width=1.8),
                    hovertemplate=f"{t}: %{{y:.2f}}<extra></extra>",
                ))
            fig_cmp.update_layout(
                **_ct(height=380),
                title=dict(
                    text=("Normalised (base=100)" if base_100 else "Raw Close Price"),
                    font=dict(size=11, color="#DDE6F0", family="Syne"),
                ),
            )
            st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

        # Performance summary table
        st.markdown('<div class="fi-section">Performance Summary</div>', unsafe_allow_html=True)
        perf_rows = []
        for t, df_t in cmp_data.items():
            if df_t.empty or len(df_t) < 2:
                continue
            c_first, c_last = float(df_t["Close"].iloc[0]), float(df_t["Close"].iloc[-1])
            pct    = (c_last - c_first) / c_first * 100
            hi     = float(df_t["High"].max()) if "High" in df_t.columns else c_last
            lo     = float(df_t["Low"].min())  if "Low"  in df_t.columns else c_last
            vol    = float(df_t["Volume"].mean()) if "Volume" in df_t.columns else 0.0
            rsi_   = float(df_t["RSI"].iloc[-1]) if "RSI" in df_t.columns else 0.0
            perf_rows.append({
                "Ticker": t,
                "Return %": f"{pct:+.2f}%",
                "Current": f"{c_last:,.2f}",
                "Period High": f"{hi:,.2f}",
                "Period Low": f"{lo:,.2f}",
                "Avg Volume": f"{vol:,.0f}",
                "RSI": f"{rsi_:.1f}",
            })
        if perf_rows:
            st.dataframe(
                pd.DataFrame(perf_rows).set_index("Ticker"),
                use_container_width=True,
            )

        # Correlation heatmap (requires at least 2 tickers with data)
        close_df = pd.DataFrame({
            t: df_t["Close"] for t, df_t in cmp_data.items() if not df_t.empty
        }).dropna()
        if len(close_df.columns) >= 2:
            st.markdown('<div class="fi-section">Correlation Heatmap</div>', unsafe_allow_html=True)
            corr = close_df.corr().round(3)
            z    = corr.values.tolist()
            lbls = list(corr.columns)

            fig_corr = go.Figure(go.Heatmap(
                z=z, x=lbls, y=lbls,
                colorscale=[
                    [0.0, "#FF3D60"], [0.5, "#0F1520"], [1.0, "#00E8A0"]
                ],
                zmid=0, zmin=-1, zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in z],
                texttemplate="%{text}",
                textfont=dict(size=10, family="JetBrains Mono"),
                hovertemplate="x: %{x}<br>y: %{y}<br>ρ = %{z:.3f}<extra></extra>",
            ))
            fig_corr.update_layout(**_ct(height=320 + len(lbls) * 20))
            st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — STOCK INFO
# ════════════════════════════════════════════════════════════════════════════
with t5:
    with st.spinner(f"Loading {ticker} info…"):
        info = _info(ticker)

    if info.get("error"):
        st.warning(f"Could not load company info for **{ticker}**: {info.get('msg','')}")
    else:
        name_h = info.get("name", ticker)
        price_d2 = _price(ticker)
        c1, c2 = st.columns([2, 1])

        with c1:
            st.markdown(f"""
                <div class="fi-card fi-card-accent">
                    <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.4rem;
                                color:#DDE6F0;margin-bottom:.3rem;">{name_h}</div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:.9rem;">
                        <span class="fi-badge badge-accent">{ticker}</span>
                        <span class="fi-badge badge-neutral">{info.get('sector','—')}</span>
                        <span class="fi-badge badge-neutral">{info.get('industry','—')}</span>
                    </div>
                    <div style="font-family:'Manrope',sans-serif;font-size:.8rem;
                                color:#7A92A8;line-height:1.72;">
                        {info.get('description','No description available.')}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="fi-card">
                    <div class="fi-title">Fundamentals</div>
                    <table style="width:100%;border-collapse:collapse;font-family:'Manrope',sans-serif;font-size:.78rem;">
                    {"".join([
                        f'<tr><td style="color:#3D5268;padding:4px 0;width:52%;">{k}</td>'
                        f'<td style="color:#DDE6F0;font-weight:600;">{v}</td></tr>'
                        for k, v in [
                            ("Market Cap",   info.get("market_cap",   "—")),
                            ("P/E Ratio",    info.get("pe_ratio",     "—")),
                            ("EPS",          info.get("eps",          "—")),
                            ("52W High",     info.get("week52_high",  "—")),
                            ("52W Low",      info.get("week52_low",   "—")),
                            ("Avg Volume",   f"{info.get('avg_volume',0):,.0f}"),
                            ("Beta",         info.get("beta",         "—")),
                            ("Dividend %",   f"{info.get('dividend_yield',0):.2f}%"),
                        ]
                    ])}
                    </table>
                </div>
            """, unsafe_allow_html=True)

        # 52-week range visual
        hi52  = float(info.get("week52_high", 0) or 0)
        lo52  = float(info.get("week52_low",  0) or 0)
        cur52 = float(price_d2.get("price", 0) or 0)
        if hi52 > lo52 > 0 and cur52 > 0:
            rng_pct = (cur52 - lo52) / (hi52 - lo52) * 100
            rng_pct = max(0, min(100, rng_pct))
            st.markdown(f"""
                <div class="fi-card" style="margin-top:.5rem;">
                    <div class="fi-title">52-Week Range</div>
                    <div style="display:flex;justify-content:space-between;
                                font-size:.72rem;color:#3D5268;margin-bottom:6px;">
                        <span>{lo52:,.2f} LOW</span>
                        <span style="color:#DDE6F0;font-weight:600;">{cur52:,.2f} NOW</span>
                        <span>{hi52:,.2f} HIGH</span>
                    </div>
                    <div style="background:#1A2535;border-radius:4px;height:6px;position:relative;">
                        <div style="position:absolute;left:0;width:{rng_pct:.1f}%;
                                    height:100%;border-radius:4px;
                                    background:linear-gradient(90deg,#00A86B,#00E8A0);"></div>
                        <div style="position:absolute;left:{rng_pct:.1f}%;
                                    transform:translateX(-50%);top:-4px;
                                    width:4px;height:14px;background:#fff;
                                    border-radius:2px;box-shadow:0 0 6px rgba(255,255,255,.6);"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Recent OHLCV table
        st.markdown('<div class="fi-section">Recent OHLCV Data</div>', unsafe_allow_html=True)
        df_recent = _ohlcv(ticker, "1 Month")
        if not df_recent.empty:
            df_show = df_recent.tail(15).copy()
            df_show.index = df_show.index.strftime("%Y-%m-%d")
            for col in df_show.columns:
                if col != "Volume":
                    df_show[col] = df_show[col].apply(lambda x: f"{x:,.2f}")
                else:
                    df_show[col] = df_show[col].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_show[::-1], use_container_width=True)
