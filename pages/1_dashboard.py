"""
pages/1_dashboard.py — Main Headline Analyzer Dashboard.
Full 7-stage ML pipeline with live results.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time

from utils.auth import require_login, current_user_id
from utils.styles import (inject_styles, sentiment_color, sentiment_badge_kind,
                           polarity_to_needle_pct, badge_html, metric_card_html)
from utils.analyser_engine import run_analysis
from utils.corporate_graph import (compute_ripple, impact_color, impact_label,
                                    relationship_icon, depth_indent, get_available_tickers)
from utils.database import save_analysis, is_in_watchlist, add_to_watchlist
from utils.stock_data import get_current_price, format_price, format_change, change_color

st.set_page_config(page_title="Dashboard · Finance Impact",
                   page_icon="⚡", layout="wide")
require_login()
inject_styles()

uid = current_user_id()

# ── AVAILABLE TICKERS ─────────────────────────────────────────────────────────
AVAILABLE = get_available_tickers()
TICKER_DISPLAY = {
    "TSLA": "Tesla, Inc.",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corp.",
    "NVDA": "NVIDIA Corp.",
    "AMZN": "Amazon.com Inc.",
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "INFY": "Infosys Ltd.",
    "WIPRO": "Wipro Ltd.",
    "HDFCBANK": "HDFC Bank Ltd.",
}

QUICK_EXAMPLES = [
    ("Tesla faces record $4.2B EU fine over autopilot safety violations", "TSLA"),
    ("Apple reports record Q4 revenue, beats by $4.5B", "AAPL"),
    ("Reliance Jio crosses 500M subscribers, stock rallies", "RELIANCE"),
    ("NVIDIA CEO Jensen Huang resigns citing personal reasons", "NVDA"),
    ("TCS Q2 revenue guidance disappoints, management warns of budget freeze", "TCS"),
    ("Amazon acquires Anthropic for $15B in landmark AI deal", "AMZN"),
    ("Infosys wins $1.8B deal with European bank", "INFY"),
    ("HDFC Bank RBI bars new credit card issuance over IT outages", "HDFCBANK"),
]

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
    <h1>⚡ Headline <span style='color:#00C8F0;'>Analyzer</span></h1>
    <p style='color:#3D5268;font-size:0.78rem;letter-spacing:0.1em;
              text-transform:uppercase;margin-bottom:1.5rem;'>
        7-Stage ML Pipeline · FinBERT · Event Classification · Corporate Ripple Effect
    </p>
""", unsafe_allow_html=True)

# ── INPUT SECTION ─────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="fi-card">', unsafe_allow_html=True)

    col_t, col_h = st.columns([1, 5])
    with col_t:
        ticker = st.selectbox(
            "Ticker",
            options=AVAILABLE,
            index=AVAILABLE.index("TSLA") if "TSLA" in AVAILABLE else 0,
            key="dash_ticker",
        )
    with col_h:
        headline = st.text_area(
            "Financial Headline",
            placeholder="Paste a news headline here… or pick a quick example below",
            height=80,
            key="dash_headline",
        )

    col_a, col_c, col_r, col_w = st.columns([2, 1, 1, 1])
    with col_a:
        analyze_btn = st.button("⚡ Analyze Impact", type="primary", use_container_width=True)
    with col_c:
        clear_btn = st.button("✕ Clear", type="secondary", use_container_width=True)
    with col_r:
        random_btn = st.button("⟳ Random", type="secondary", use_container_width=True)
    with col_w:
        watch_btn = st.button("＋ Watchlist", type="secondary", use_container_width=True)

    # Quick examples
    st.markdown('<div class="section-label" style="margin-top:1rem;">Quick Examples</div>',
                unsafe_allow_html=True)
    ex_cols = st.columns(4)
    for i, (ex_hl, ex_t) in enumerate(QUICK_EXAMPLES):
        with ex_cols[i % 4]:
            label = ex_hl[:42] + "…" if len(ex_hl) > 42 else ex_hl
            if st.button(label, key=f"ex_{i}", use_container_width=True, type="secondary"):
                st.session_state["dash_headline"] = ex_hl
                st.session_state["dash_ticker"]   = ex_t
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── HANDLE CONTROLS ───────────────────────────────────────────────────────────
if clear_btn:
    st.session_state.pop("dash_headline", None)
    st.session_state.pop("analysis_result", None)
    st.rerun()

if random_btn:
    import random
    ex = random.choice(QUICK_EXAMPLES)
    st.session_state["dash_headline"] = ex[0]
    st.session_state["dash_ticker"]   = ex[1]
    st.rerun()

if watch_btn and ticker:
    company = TICKER_DISPLAY.get(ticker, ticker)
    if add_to_watchlist(uid, ticker, company):
        st.success(f"Added {ticker} to watchlist!")
    else:
        st.info(f"{ticker} already in watchlist.")

# ── RUN ANALYSIS ──────────────────────────────────────────────────────────────
if analyze_btn and headline and headline.strip():
    with st.spinner("Running analysis pipeline…"):
        result = run_analysis(headline.strip(), ticker)
        st.session_state["analysis_result"] = result
        save_analysis(uid, ticker, headline.strip(), result)

elif analyze_btn:
    st.warning("Please enter a headline first.")

# ── DISPLAY RESULTS ───────────────────────────────────────────────────────────
result = st.session_state.get("analysis_result")

if result is None:
    st.markdown("""
        <div style='text-align:center;padding:3rem;color:#3D5268;'>
            <div style='font-size:2.5rem;margin-bottom:1rem;opacity:0.3;'>◈</div>
            <div style='font-family:Syne,sans-serif;font-size:1rem;
                        color:#7A92A8;margin-bottom:0.5rem;'>Ready to Analyze</div>
            <div style='font-size:0.8rem;line-height:1.65;max-width:320px;margin:0 auto;'>
                Enter a financial headline above, pick a quick example,
                or click the news feed to analyze live headlines.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── RESULT IS READY ───────────────────────────────────────────────────────────
pol      = result["polarity"]
cat      = result["category"]
label    = result["label"]
conf     = result["confidence"]
rel      = result["relevance_score"]
cred     = result["credibility"]
evt      = result["event_type"]
is_rum   = result["is_rumour"]
s_color  = sentiment_color(cat)
s_kind   = sentiment_badge_kind(cat)

# ── STAT CARDS ROW ────────────────────────────────────────────────────────────
st.markdown('<div class="stat-row">', unsafe_allow_html=True)
color_map = {
    "STRONG_NEGATIVE": "#FF3D60",
    "NEGATIVE":        "#FF7D35",
    "NEUTRAL":         "#7A92A8",
    "POSITIVE":        "#00E8A0",
    "STRONG_POSITIVE": "#00E8A0",
}
cards_html = (
    metric_card_html("Sentiment Score", f"{pol:+.2f}", label,
                     color_map.get(cat, "#7A92A8"), color_map.get(cat, "#7A92A8")) +
    metric_card_html("FinBERT Confidence", f"{conf:.0%}", "Model certainty",
                     "#00C8F0", "#00C8F0") +
    metric_card_html("Relevance", f"{rel:.0%}", "Direct company news",
                     "#FFD060", "#FFD060") +
    metric_card_html("Credibility", f"{cred:.0%}",
                     "Rumour detected" if is_rum else "Confirmed source",
                     "#FF7D35" if is_rum else "#00E8A0",
                     "#FF7D35" if is_rum else "#00E8A0") +
    metric_card_html("Entities Hit", str(len(result["ripple_tree"])),
                     "In corporate graph", "#9B6DFF", "#9B6DFF")
)
st.markdown(cards_html + '</div>', unsafe_allow_html=True)

# ── MAIN RESULTS TABS ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Sentiment",
    "🌐 Ripple Effect",
    "📈 Historical",
    "🔍 Explainability",
    "📋 Full Report",
])

# ═══════════════════════════════════════════════════════
# TAB 1 — SENTIMENT
# ═══════════════════════════════════════════════════════
with tab1:
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown(f"""
            <div class="fi-card">
                <div class="fi-card-title">Sentiment Impact Analysis</div>
                <div style='display:flex;align-items:center;gap:16px;'>
                    <div style='text-align:center;min-width:90px;'>
                        <div style='font-family:Syne,sans-serif;font-weight:800;
                                    font-size:2.8rem;color:{s_color};line-height:1;'>
                            {pol:+.2f}
                        </div>
                        <div style='font-size:0.65rem;color:#3D5268;
                                    letter-spacing:0.1em;text-transform:uppercase;
                                    margin-top:4px;'>Polarity</div>
                    </div>
                    <div style='flex:1;'>
                        <div style='display:flex;justify-content:space-between;
                                    font-size:0.65rem;color:#3D5268;margin-bottom:6px;'>
                            <span>Strong Neg</span><span>Neutral</span><span>Strong Pos</span>
                        </div>
                        <div style='height:10px;border-radius:5px;
                                    background:linear-gradient(90deg,
                                        #AA1133 0%,#FF3D60 20%,#FF7D35 35%,
                                        #444 50%,
                                        #00A86B 65%,#00E8A0 80%,#00FF88 100%);
                                    position:relative;margin-bottom:4px;'>
                            <div style='position:absolute;top:-5px;
                                        left:{polarity_to_needle_pct(pol)}%;
                                        width:4px;height:20px;background:#fff;
                                        border-radius:2px;transform:translateX(-50%);
                                        box-shadow:0 0 10px rgba(255,255,255,0.8);'>
                            </div>
                        </div>
                        <div style='display:flex;justify-content:space-between;
                                    font-size:0.65rem;color:#3D5268;'>
                            <span>−1.0</span><span>−0.5</span><span>0.0</span>
                            <span>+0.5</span><span>+1.0</span>
                        </div>
                    </div>
                    <div>
                        {badge_html(label, s_kind)}
                        <div style='font-size:0.7rem;color:#3D5268;
                                    margin-top:6px;text-align:right;'>
                            {evt}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Reason box
        st.markdown(f"""
            <div class="reason-box">
                {result['reason']}
            </div>
        """, unsafe_allow_html=True)

        # Warnings
        if result["is_rumour"]:
            st.warning("⚠️ Rumour signals detected — confidence is dampened accordingly.")
        if not result["is_relevant"]:
            st.info(f"ℹ️ This headline may not be directly about {ticker}.")

        # Jargon tags
        if result["jargon_detected"]:
            st.markdown('<div class="section-label">Financial Jargon Detected</div>',
                        unsafe_allow_html=True)
            tags = " ".join(badge_html(j, "purple") for j in result["jargon_detected"])
            st.markdown(tags, unsafe_allow_html=True)

    with c2:
        # Confidence bars
        st.markdown('<div class="fi-card">', unsafe_allow_html=True)
        st.markdown('<div class="fi-card-title">Confidence Breakdown</div>',
                    unsafe_allow_html=True)

        bars = [
            ("FinBERT Score",    conf,  "#00C8F0"),
            ("Relevance",        rel,   "#FFD060"),
            ("Credibility",      cred,  "#FF7D35" if is_rum else "#00E8A0"),
        ]

        hist_pred = result.get("hist_prediction", {})
        if hist_pred:
            h_acc = hist_pred.get("directional_acc", 0) / 100
            bars.append(("Hist. Accuracy", h_acc, "#9B6DFF"))

        for bar_label, val, color in bars:
            pct = int(val * 100)
            st.markdown(f"""
                <div style='margin-bottom:12px;'>
                    <div style='display:flex;justify-content:space-between;
                                font-size:0.72rem;color:#7A92A8;margin-bottom:5px;'>
                        <span>{bar_label}</span>
                        <span style='color:{color};font-family:Syne,sans-serif;
                                     font-weight:600;'>{pct}%</span>
                    </div>
                    <div style='height:4px;background:#0F1520;border-radius:2px;overflow:hidden;'>
                        <div style='height:100%;width:{pct}%;background:{color};
                                    border-radius:2px;transition:width 1s ease;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Live stock price
        price_data = get_current_price(ticker)
        if not price_data.get("error"):
            chg_c = change_color(price_data)
            st.markdown(f"""
                <div class="fi-card" style="margin-top:1rem;">
                    <div class="fi-card-title">{ticker} Live Price</div>
                    <div style='font-family:Syne,sans-serif;font-weight:800;
                                font-size:1.6rem;color:#DDE6F0;'>
                        {format_price(price_data)}
                    </div>
                    <div style='font-size:0.8rem;color:{chg_c};margin-top:4px;'>
                        {format_change(price_data)} today
                    </div>
                </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2 — RIPPLE EFFECT
# ═══════════════════════════════════════════════════════
with tab2:
    ripple = result.get("ripple_tree", [])

    if not ripple:
        st.info("No corporate hierarchy data available for this ticker.")
    else:
        st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:1rem;'>
                <span style='font-family:Syne,sans-serif;font-weight:600;
                             font-size:0.9rem;'>Corporate Ripple Effect</span>
                {badge_html(f"{len(ripple)} entities", "red" if pol < 0 else "green")}
                <span style='font-size:0.75rem;color:#3D5268;'>
                    Impact propagates by ownership % × relationship type × depth decay
                </span>
            </div>
        """, unsafe_allow_html=True)

        for node in ripple:
            depth     = node["depth"]
            ico       = relationship_icon(node["relationship"])
            imp       = node["impact"]
            imp_color = impact_color(imp)
            imp_label = impact_label(imp)
            indent    = depth * 24

            is_root_style = (
                "border-color:#00C8F0;background:rgba(0,200,240,0.03);"
                if node["is_root"] else ""
            )
            dashed = (
                "border-style:dashed;"
                if node["relationship"] in ("joint_venture", "strategic_investment", "investment")
                else ""
            )

            st.markdown(f"""
                <div class="tree-node" style="margin-left:{indent}px;{is_root_style}{dashed}">
                    <div style='font-size:1.2rem;width:28px;text-align:center;
                                flex-shrink:0;'>{ico}</div>
                    <div style='flex:1;min-width:0;'>
                        <div style='font-family:Syne,sans-serif;font-weight:600;
                                    font-size:0.82rem;color:#DDE6F0;'>
                            {node['name']}
                        </div>
                        <div style='font-size:0.7rem;color:#3D5268;white-space:nowrap;
                                    overflow:hidden;text-overflow:ellipsis;'>
                            {node.get('description', node.get('sector', ''))}
                        </div>
                    </div>
                    <div style='text-align:right;flex-shrink:0;'>
                        <div style='font-family:Syne,sans-serif;font-weight:700;
                                    font-size:0.85rem;color:{imp_color};'>
                            {imp:+.3f}
                        </div>
                        <div style='font-size:0.65rem;color:#3D5268;'>
                            {imp_label} · {node['ownership']}% stake
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Plotly bar chart of ripple impacts
        st.markdown("<br>", unsafe_allow_html=True)
        names  = [n["name"][:30] for n in ripple]
        imps   = [n["impact"] for n in ripple]
        colors = [impact_color(i) for i in imps]

        fig = go.Figure(go.Bar(
            x=imps, y=names, orientation="h",
            marker_color=colors,
            text=[f"{i:+.3f}" for i in imps],
            textposition="outside",
        ))
        fig.update_layout(
            paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
            font=dict(color="#7A92A8", size=11),
            xaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
                       title="Impact Score"),
            yaxis=dict(gridcolor="#1A2535"),
            margin=dict(l=10, r=60, t=20, b=20),
            height=max(200, len(ripple) * 38),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 3 — HISTORICAL MATCHES
# ═══════════════════════════════════════════════════════
with tab3:
    similar = result.get("similar_headlines", pd.DataFrame())
    hist_pred = result.get("hist_prediction", {})

    if similar.empty:
        st.info("No similar historical headlines found.")
    else:
        st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:1rem;'>
                <span style='font-family:Syne,sans-serif;font-weight:600;
                             font-size:0.9rem;'>Similar Historical Headlines</span>
                {badge_html(f"{len(similar)} matches found", "neutral")}
            </div>
        """, unsafe_allow_html=True)

        for _, row in similar.iterrows():
            t3   = row.get("t3_move_pct", None)
            sim  = row.get("similarity", 0)
            sent = row.get("sentiment", "NEUTRAL")
            sc   = sentiment_color(sent)
            t3_s = f"{t3:+.1f}%" if pd.notna(t3) else "N/A"
            t3_c = "#00E8A0" if (t3 or 0) > 0 else "#FF3D60"

            st.markdown(f"""
                <div class="hist-item">
                    <div style='font-size:0.72rem;color:#3D5268;
                                min-width:80px;padding-top:2px;'>
                        {row.get('Date', 'N/A')}
                    </div>
                    <div style='flex:1;'>
                        <div style='font-size:0.82rem;color:#7A92A8;line-height:1.55;'>
                            {row.get('Headline', '')}
                        </div>
                        <div style='margin-top:5px;'>
                            {badge_html(row.get('event_type', 'News'), 'neutral')}
                        </div>
                    </div>
                    <div style='text-align:right;flex-shrink:0;min-width:80px;'>
                        <div style='font-family:Syne,sans-serif;font-weight:700;
                                    font-size:0.9rem;color:{t3_c};'>{t3_s}</div>
                        <div style='font-size:0.65rem;color:#3D5268;'>
                            T+3 move · {sim:.0f}% sim
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Prediction box
        if hist_pred:
            avg     = hist_pred.get("avg_move", 0)
            r_low   = hist_pred.get("range_low", avg)
            r_high  = hist_pred.get("range_high", avg)
            d_acc   = hist_pred.get("directional_acc", 0)
            n       = hist_pred.get("sample_count", 0)
            p_color = "#00E8A0" if avg >= 0 else "#FF3D60"

            st.markdown(f"""
                <div class="pred-box">
                    <div class="pred-label">T+3 Prediction · Based on {n} Matches</div>
                    <div class="pred-value" style="color:{p_color};">
                        Likely range: {r_low:+.1f}% to {r_high:+.1f}%
                    </div>
                    <div style='font-size:0.72rem;color:#3D5268;margin-top:4px;'>
                        Historical avg: {avg:+.1f}% ·
                        Directional accuracy: {d_acc:.0f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Chart: scatter of historical outcomes
        if "t3_move_pct" in similar.columns and "similarity" in similar.columns:
            fig2 = go.Figure()
            for _, row in similar.iterrows():
                t3  = row.get("t3_move_pct", 0) or 0
                sim = row.get("similarity", 50)
                col = "#00E8A0" if t3 >= 0 else "#FF3D60"
                fig2.add_trace(go.Scatter(
                    x=[sim], y=[t3],
                    mode="markers+text",
                    marker=dict(size=14, color=col, opacity=0.85),
                    text=[row.get("Ticker", "")],
                    textposition="top center",
                    showlegend=False,
                ))
            fig2.update_layout(
                paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
                font=dict(color="#7A92A8", size=11),
                xaxis=dict(title="Similarity %", gridcolor="#1A2535"),
                yaxis=dict(title="Actual T+3 Move %", gridcolor="#1A2535",
                           zerolinecolor="#22334A"),
                margin=dict(l=10, r=10, t=20, b=30),
                height=300,
            )
            st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 4 — EXPLAINABILITY (SHAP)
# ═══════════════════════════════════════════════════════
with tab4:
    attrs = result.get("word_attributions", [])

    st.markdown("""
        <div style='font-size:0.78rem;color:#7A92A8;margin-bottom:1rem;line-height:1.65;'>
            <strong style='color:#DDE6F0;'>Word Attribution Analysis</strong> —
            Shows which words in the headline drove the sentiment score up or down.
            Based on weighted financial lexicon (SHAP-style attribution).
        </div>
    """, unsafe_allow_html=True)

    if not attrs:
        st.info("No significant attributions found for this headline.")
    else:
        max_contrib = max(abs(a["contribution"]) for a in attrs) if attrs else 1

        for a in attrs:
            contr  = a["contribution"]
            width  = int(abs(contr) / max_contrib * 100)
            color  = "#00E8A0" if contr > 0 else "#FF3D60"
            direct = "▲" if contr > 0 else "▼"
            sign   = "+" if contr > 0 else ""

            st.markdown(f"""
                <div style='display:flex;align-items:center;gap:12px;
                            padding:8px 12px;border-radius:8px;
                            background:#0F1520;border:1px solid #1A2535;
                            margin-bottom:6px;'>
                    <div style='font-family:Syne,sans-serif;font-weight:700;
                                font-size:0.85rem;color:{color};min-width:20px;'>
                        {direct}
                    </div>
                    <div style='font-family:Syne,sans-serif;font-weight:600;
                                font-size:0.82rem;color:#DDE6F0;min-width:120px;'>
                        "{a['word']}"
                    </div>
                    <div style='flex:1;height:6px;background:#07090D;
                                border-radius:3px;overflow:hidden;'>
                        <div style='height:100%;width:{width}%;
                                    background:{color};border-radius:3px;'></div>
                    </div>
                    <div style='font-family:Syne,sans-serif;font-weight:700;
                                font-size:0.8rem;color:{color};min-width:48px;
                                text-align:right;'>
                        {sign}{contr:.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Macro context
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="fi-card">
            <div class="fi-card-title">Macro Context Injection</div>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div style='font-size:0.82rem;color:#7A92A8;'>
                    {result.get('macro_description', '')}
                </div>
                <div style='font-family:Syne,sans-serif;font-weight:700;
                            font-size:1.1rem;color:#FFD060;'>
                    ×{result.get('macro_factor', 1.0):.2f}
                </div>
            </div>
            <div style='font-size:0.72rem;color:#3D5268;margin-top:6px;'>
                Amplifier applied to base FinBERT score of
                <span style='color:#DDE6F0;'>{result['raw_polarity']:+.3f}</span>
                → final score
                <span style='color:{s_color};'>{pol:+.3f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 5 — FULL REPORT
# ═══════════════════════════════════════════════════════
with tab5:
    st.markdown(f"""
        <div class="fi-card">
            <div class="fi-card-title">Full Analysis Report</div>
            <div style='font-size:0.72rem;color:#3D5268;margin-bottom:1rem;'>
                Analyzed at {result.get('analyzed_at', '')[:19].replace('T', ' ')} UTC
            </div>
            <table style='width:100%;border-collapse:collapse;font-size:0.8rem;'>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;width:40%;'>Headline</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{result['headline']}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Ticker</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{result['ticker']}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Sentiment Category</td>
                    <td style='padding:8px 0;color:{s_color};font-family:Syne,sans-serif;
                               font-weight:700;'>{label}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Polarity Score</td>
                    <td style='padding:8px 0;color:{s_color};font-family:Syne,sans-serif;
                               font-weight:700;'>{pol:+.3f}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Raw FinBERT Polarity</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{result['raw_polarity']:+.3f}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>FinBERT Confidence</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{conf:.1%}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Relevance Score</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{rel:.1%}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Credibility Score</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{cred:.1%}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Event Type</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>{evt}</td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Event Multiplier</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>
                        ×{result.get('event_multiplier', 1.0):.2f}
                    </td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Rumour Detected</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>
                        {"⚠️ Yes" if is_rum else "✓ No"}
                    </td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Macro Factor</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>
                        ×{result.get('macro_factor', 1.0):.2f} —
                        {result.get('macro_description', '')}
                    </td>
                </tr>
                <tr style='border-bottom:1px solid #1A2535;'>
                    <td style='padding:8px 0;color:#3D5268;'>Entities Detected</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>
                        {', '.join(result.get('detected_entities', [])) or 'None'}
                    </td>
                </tr>
                <tr>
                    <td style='padding:8px 0;color:#3D5268;'>Jargon Detected</td>
                    <td style='padding:8px 0;color:#DDE6F0;'>
                        {', '.join(result.get('jargon_detected', [])) or 'None'}
                    </td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)
