"""
pages/news.py — Live RSS News Feed.
"""

import streamlit as st
import plotly.graph_objects as go

from utils.auth       import require_login
from utils.styles     import inject_styles, badge_html, sentiment_color
from utils.news_fetcher import fetch_rss_news, sentiment_dot_color

st.set_page_config(page_title="News Feed · Finance Impact", layout="wide")
st.session_state["_current_page"] = "news"
require_login()
inject_styles()

st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1>Live <span style="color:#00C8F0;">News Feed</span></h1>
        <p style="color:#3D5268;font-size:0.72rem;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0;">
            Reuters &middot; Bloomberg &middot; ET Markets &middot; Moneycontrol &middot; CNBC &middot; Livemint
        </p>
    </div>
""", unsafe_allow_html=True)

col_f, col_t, col_r = st.columns([3, 2, 1])
with col_f:
    sentiment_filter = st.selectbox(
        "Filter by Sentiment",
        ["All", "STRONG_POSITIVE", "POSITIVE", "NEUTRAL", "NEGATIVE", "STRONG_NEGATIVE"],
        key="feed_sent_filter",
    )
with col_t:
    ticker_filter = st.selectbox(
        "Filter by Ticker",
        ["All", "TSLA", "AAPL", "GOOGL", "MSFT", "NVDA", "AMZN",
         "RELIANCE", "TCS", "INFY", "WIPRO", "HDFCBANK", "GENERAL"],
        key="feed_ticker_filter",
    )
with col_r:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh = st.button("Refresh", type="secondary", use_container_width=True)

with st.spinner("Fetching latest headlines..."):
    df = fetch_rss_news(max_items=50)

if sentiment_filter != "All":
    df = df[df["sentiment"] == sentiment_filter]
if ticker_filter != "All":
    df = df[df["tickers"].str.contains(ticker_filter, na=False)]

if df.empty:
    st.info("No headlines found for the selected filters.")
    st.stop()

tot   = len(df)
n_pos = len(df[df["polarity"] >  0.15])
n_neg = len(df[df["polarity"] < -0.15])
n_neu = tot - n_pos - n_neg
n_rum = int(df["is_rumour"].sum())

c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("Total Headlines", tot)
with c2: st.metric("Positive",  n_pos)
with c3: st.metric("Negative",  n_neg)
with c4: st.metric("Neutral",   n_neu)
with c5: st.metric("Rumours",   n_rum)

st.markdown("<br>", unsafe_allow_html=True)

col_feed, col_side = st.columns([3, 1])

with col_feed:
    for _, row in df.iterrows():
        pol      = row.get("polarity", 0)
        sent     = row.get("sentiment", "NEUTRAL")
        dot_c    = sentiment_dot_color(pol)
        is_rum   = row.get("is_rumour", False)
        tickers_ = row.get("tickers", "GENERAL")
        title    = row.get("title", "")
        source   = row.get("source", "")
        pub      = row.get("published", "")
        link     = row.get("link", "")

        rum_badge = badge_html("Rumour", "orange") if is_rum else ""
        pol_kind  = "red" if pol < -0.1 else "green" if pol > 0.1 else "neutral"
        src_link  = f'<a href="{link}" target="_blank" style="font-size:0.68rem;color:#3D5268;margin-left:auto;">Source</a>' if link else ""

        st.markdown(f"""
            <div style="padding:12px;background:#111927;border-radius:10px;
                        border:1px solid #1A2535;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <span style="font-size:0.68rem;color:#3D5268;
                                 letter-spacing:0.08em;text-transform:uppercase;">{source}</span>
                    <span style="width:3px;height:3px;background:#3D5268;
                                 border-radius:50%;display:inline-block;"></span>
                    <span style="font-size:0.68rem;color:#3D5268;">{pub}</span>
                    <span style="margin-left:auto;width:8px;height:8px;border-radius:50%;
                                 background:{dot_c};box-shadow:0 0 6px {dot_c};"></span>
                </div>
                <div style="font-size:0.85rem;color:#DDE6F0;line-height:1.55;margin-bottom:8px;">
                    {title}
                </div>
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                    {' '.join(badge_html(t, 'accent') for t in tickers_.split(', ') if t)}
                    {badge_html(f"{pol:+.2f}", pol_kind)}
                    {rum_badge}
                    {src_link}
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button(f"Analyze: {title[:55]}...", key=f"an_{hash(title)}",
                     type="secondary", use_container_width=False):
            t_use = tickers_.split(", ")[0] if tickers_ != "GENERAL" else "TSLA"
            st.session_state["dash_ticker"]   = t_use
            st.session_state["dash_headline"] = title
            st.switch_page("pages/dashboard.py")

with col_side:
    st.markdown('<div class="fi-card">', unsafe_allow_html=True)
    st.markdown('<div class="fi-card-title">Sentiment Mix</div>', unsafe_allow_html=True)
    sent_counts = df["sentiment"].value_counts()
    color_map = {
        "STRONG_POSITIVE": "#00E8A0", "POSITIVE": "#00A86B", "NEUTRAL": "#3D5268",
        "NEGATIVE": "#FF7D35", "STRONG_NEGATIVE": "#FF3D60",
    }
    fig = go.Figure(go.Pie(
        labels=sent_counts.index.tolist(),
        values=sent_counts.values.tolist(),
        marker_colors=[color_map.get(l, "#7A92A8") for l in sent_counts.index],
        hole=0.55, textinfo="label+percent",
        textfont=dict(size=10),
    ))
    fig.update_layout(
        paper_bgcolor="#111927", plot_bgcolor="#111927",
        font=dict(color="#7A92A8", size=10),
        margin=dict(l=0, r=0, t=0, b=0),
        height=220, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="fi-card" style="margin-top:1rem;">', unsafe_allow_html=True)
    st.markdown('<div class="fi-card-title">Strongest Signals</div>', unsafe_allow_html=True)
    top = df.nlargest(3, "polarity") if len(df) >= 3 else df
    for _, row in top.iterrows():
        p = row.get("polarity", 0)
        c = "#00E8A0" if p > 0 else "#FF3D60"
        st.markdown(f"""
            <div style="padding:7px 0;border-bottom:1px solid #1A2535;">
                <div style="font-size:0.72rem;color:#7A92A8;line-height:1.4;">
                    {row.get('title','')[:60]}...
                </div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:0.8rem;color:{c};margin-top:3px;">{p:+.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
