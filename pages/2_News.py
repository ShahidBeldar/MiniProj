"""
pages/2_News.py — Live RSS News Feed with click-to-analyze.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go


from ui.theme      import inject_css
from ui.auth       import require_login
from ui.nav        import render_sidebar
from ui.components import page_header, badge, news_card, sentiment_color
from core.feeds    import fetch_news, sentiment_dot_color

inject_css()
require_login()
st.session_state["_page"] = "news"
render_sidebar("news")

st.markdown(page_header(
    'Live <span style="color:#00C8F0;">News Feed</span>',
    "Reuters · Bloomberg · ET Markets · Moneycontrol · CNBC · Yahoo Finance",
), unsafe_allow_html=True)

# ── FILTERS ───────────────────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
with f1:
    sf = st.selectbox("Sentiment Filter",
                      ["All","STRONG_POSITIVE","POSITIVE","NEUTRAL","NEGATIVE","STRONG_NEGATIVE"],
                      key="_nf_sent")
with f2:
    tf = st.selectbox("Ticker Filter",
                      ["All","TSLA","AAPL","GOOGL","MSFT","NVDA","AMZN",
                       "RELIANCE","TCS","INFY","WIPRO","HDFCBANK","GENERAL"],
                      key="_nf_tkr")
with f3:
    rumour_only = st.toggle("Rumours Only", value=False, key="_nf_rum")
with f4:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh = st.button("Refresh Feed", type="secondary", use_container_width=True, key="_nf_ref")

if refresh:
    st.cache_data.clear()

@st.cache_data(ttl=600, show_spinner="Fetching headlines…")
def _load():
    return fetch_news(max_items=60)

df = _load()

if sf != "All":       df = df[df["sentiment"] == sf]
if tf != "All":       df = df[df["tickers"].str.contains(tf, na=False)]
if rumour_only:       df = df[df["is_rumour"] == True]

if df.empty:
    st.info("No headlines match the selected filters.")
    st.stop()

# ── METRICS ───────────────────────────────────────────────────────────────────
tot   = len(df)
n_pos = int((df["polarity"] >  0.1).sum())
n_neg = int((df["polarity"] < -0.1).sum())
n_rum = int(df["is_rumour"].sum())
m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("Headlines",   tot)
with m2: st.metric("Bullish",     n_pos)
with m3: st.metric("Bearish",     n_neg)
with m4: st.metric("Neutral",     tot - n_pos - n_neg)
with m5: st.metric("Rumours",     n_rum)

st.markdown("<br>", unsafe_allow_html=True)

# ── TWO-COLUMN LAYOUT ─────────────────────────────────────────────────────────
feed_col, side_col = st.columns([3, 1])

with feed_col:
    for i, row in df.iterrows():
        title   = row.get("title", "")
        pol     = float(row.get("polarity", 0))
        sent    = row.get("sentiment", "NEUTRAL")
        tickers = row.get("tickers", "GENERAL")
        src     = row.get("source", "")
        pub     = row.get("published", "")
        link    = row.get("link", "")
        is_rum  = bool(row.get("is_rumour", False))

        st.markdown(news_card(title, src, pub, pol, tickers, is_rum, link),
                    unsafe_allow_html=True)

        btn_lbl = title[:65] + ("…" if len(title) > 65 else "")
        if st.button(f"Analyze: {btn_lbl}", key=f"_nf_an_{i}",
                     type="secondary", use_container_width=False):
            t_use = tickers.split(", ")[0] if tickers not in ("GENERAL", "") else "TSLA"
            st.session_state["_pending_hl"] = title
            st.session_state["_pending_t"]  = t_use
            st.switch_page("pages/1_Dashboard.py")

with side_col:
    # Sentiment donut
    st.markdown('<div class="fi-card"><div class="fi-title">Sentiment Mix</div>',
                unsafe_allow_html=True)
    sc_counts = df["sentiment"].value_counts()
    cmap = {"STRONG_POSITIVE":"#00E8A0","POSITIVE":"#00A86B","NEUTRAL":"#3D5268",
            "NEGATIVE":"#FF7D35","STRONG_NEGATIVE":"#FF3D60"}
    fig = go.Figure(go.Pie(
        labels=sc_counts.index.tolist(),
        values=sc_counts.values.tolist(),
        marker_colors=[cmap.get(l, "#7A92A8") for l in sc_counts.index],
        hole=0.58,
        textinfo="label+percent",
        textfont=dict(size=8.5, family="Manrope"),
    ))
    fig.update_layout(
        paper_bgcolor="#111927", plot_bgcolor="#111927",
        font=dict(color="#7A92A8", size=9, family="Manrope"),
        margin=dict(l=0, r=0, t=5, b=0),
        height=215,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Top signals
    st.markdown('<div class="fi-card" style="margin-top:.85rem;">'
                '<div class="fi-title">Strongest Signals</div>', unsafe_allow_html=True)
    top5 = df.nlargest(5, "polarity") if len(df) >= 5 else df
    for _, row in top5.iterrows():
        p = float(row.get("polarity", 0))
        c = "#00E8A0" if p > 0 else "#FF3D60"
        st.markdown(f"""
            <div style="padding:7px 0;border-bottom:1px solid #1A2535;">
                <div style="font-size:.7rem;color:#7A92A8;line-height:1.45;
                            font-family:'Manrope',sans-serif;">
                    {row.get('title','')[:60]}…</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:.78rem;color:{c};margin-top:3px;">{p:+.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Ticker coverage
    st.markdown('<div class="fi-card" style="margin-top:.85rem;">'
                '<div class="fi-title">Ticker Coverage</div>', unsafe_allow_html=True)
    all_tkrs: list[str] = []
    for t in df["tickers"].fillna(""):
        all_tkrs.extend([x.strip() for x in t.split(",") if x.strip() and x.strip() != "GENERAL"])
    import pandas as pd
    if all_tkrs:
        tkr_counts = pd.Series(all_tkrs).value_counts().head(8)
        for tkr, cnt in tkr_counts.items():
            st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:4px 0;
                            border-bottom:1px solid #1A2535;">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:.72rem;
                                 color:#00C8F0;">{tkr}</span>
                    <span style="font-family:'Manrope',sans-serif;font-size:.72rem;
                                 color:#3D5268;">{cnt}</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
