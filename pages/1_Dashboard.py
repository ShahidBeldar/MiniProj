"""
pages/1_Dashboard.py — Headline Analyzer (7-stage ML pipeline).

Session-state / widget-key safety:
  Widget keys: _dash_hl, _dash_t
  Pending pre-fill: _pending_hl, _pending_t  (flushed BEFORE widget render)
  Results: _result (dict)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


from ui.theme      import inject_css
from ui.auth       import require_login, uid
from ui.components import (
    page_header, badge, stat_box, stat_row, polarity_bar,
    mini_progress_bar, attribution_bar, ripple_node, hist_row,
    live_price_card, sentiment_color, sentiment_badge_kind,
)
from core.engine import run_analysis
from core.graph  import get_tickers, impact_color
from db.ops      import save_analysis, add_watch, in_watchlist
from core.stocks import (
    get_price, get_ohlcv_with_indicators, get_index_prices,
    fmt_price, fmt_change, chg_color, rsi_signal,
    PERIOD_OPTIONS, MARKET_INDICES,
)
from plotly.subplots import make_subplots

inject_css()
require_login()
st.session_state["_page"] = "dashboard"

_uid    = uid()
TICKERS = get_tickers()

_TKR_NAME = {
    "TSLA":"Tesla, Inc.","AAPL":"Apple Inc.","GOOGL":"Alphabet Inc.",
    "MSFT":"Microsoft Corp.","NVDA":"NVIDIA Corp.","AMZN":"Amazon.com Inc.",
    "RELIANCE":"Reliance Industries","TCS":"Tata Consultancy Services",
    "INFY":"Infosys Ltd.","WIPRO":"Wipro Ltd.","HDFCBANK":"HDFC Bank Ltd.",
}

_EXAMPLES = [
    ("Tesla faces record $4.2B EU fine over autopilot safety violations",             "TSLA"),
    ("Apple reports record Q4 revenue, beats estimates by $4.5B",                     "AAPL"),
    ("Reliance Jio crosses 500M subscribers, stock rallies 4%",                       "RELIANCE"),
    ("NVIDIA CEO Jensen Huang resigns citing personal health reasons",                 "NVDA"),
    ("TCS Q2 revenue guidance disappoints, management warns of budget freeze",         "TCS"),
    ("Amazon acquires Anthropic for $15B in landmark AI deal",                        "AMZN"),
    ("Infosys wins $1.8B deal with European bank for core modernisation",             "INFY"),
    ("HDFC Bank barred from issuing new credit cards due to IT governance failures",  "HDFCBANK"),
    ("Microsoft Azure revenue grows 29% — AI workloads accelerate cloud growth",      "MSFT"),
    ("Google faces $5B EU fine over Android antitrust practices",                     "GOOGL"),
    ("WIPRO announces $500M buyback amid strong free cash flow generation",            "WIPRO"),
    ("Infosys cuts annual revenue guidance for second consecutive quarter",            "INFY"),
]

# ── FLUSH PENDING PRE-FILL ────────────────────────────────────────────────────
# CRITICAL: must happen BEFORE any widget with keys _dash_hl / _dash_t is created.
if "_pending_hl" in st.session_state:
    st.session_state["_dash_hl"] = st.session_state.pop("_pending_hl")
if "_pending_t" in st.session_state:
    st.session_state["_dash_t"]  = st.session_state.pop("_pending_t")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(page_header(
    'Headline <span style="color:#00C8F0;">Analyzer</span>',
    "7-Stage ML Pipeline · FinBERT · Event Classification · Corporate Ripple Effect"
), unsafe_allow_html=True)

# ── INPUT CARD ────────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="fi-card fi-card-accent">', unsafe_allow_html=True)
    col_t, col_h = st.columns([1, 5])
    with col_t:
        _default_t = st.session_state.get("_dash_t", "TSLA")
        _t_idx     = TICKERS.index(_default_t) if _default_t in TICKERS else 0
        ticker     = st.selectbox("Ticker", TICKERS, index=_t_idx, key="_dash_t")
    with col_h:
        headline = st.text_area(
            "Financial Headline",
            placeholder="Paste a financial headline or pick one below…",
            height=85,
            key="_dash_hl",
        )

    ca, cb, cc, cd = st.columns([2, 1, 1, 1])
    with ca:
        analyze_btn = st.button("Analyze Impact", type="primary",
                                use_container_width=True, key="_btn_analyze")
    with cb:
        clear_btn   = st.button("Clear",          type="secondary",
                                use_container_width=True, key="_btn_clear")
    with cc:
        random_btn  = st.button("Random Example", type="secondary",
                                use_container_width=True, key="_btn_random")
    with cd:
        watch_btn   = st.button(
            "In Watchlist" if in_watchlist(_uid, ticker) else "Add to Watchlist",
            type="secondary",
            use_container_width=True,
            key="_btn_watch",
        )

    # Quick examples
    st.markdown('<div class="fi-section" style="margin-top:.9rem;">Quick Examples</div>',
                unsafe_allow_html=True)
    ex_cols = st.columns(4)
    for i, (ex_hl, ex_t) in enumerate(_EXAMPLES):
        with ex_cols[i % 4]:
            lbl = ex_hl[:42] + ("…" if len(ex_hl) > 42 else "")
            if st.button(lbl, key=f"_ex_{i}", use_container_width=True, type="secondary"):
                st.session_state["_pending_hl"] = ex_hl
                st.session_state["_pending_t"]  = ex_t
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── CONTROL HANDLERS ─────────────────────────────────────────────────────────
if clear_btn:
    for k in ("_dash_hl","_dash_t","_result"):
        st.session_state.pop(k, None)
    st.rerun()

if random_btn:
    ex = random.choice(_EXAMPLES)
    st.session_state["_pending_hl"] = ex[0]
    st.session_state["_pending_t"]  = ex[1]
    st.rerun()

if watch_btn and ticker:
    if not in_watchlist(_uid, ticker):
        add_watch(_uid, ticker, _TKR_NAME.get(ticker, ticker))
        st.success(f"{ticker} added to watchlist.")
    else:
        st.info(f"{ticker} is already in your watchlist.")

if analyze_btn:
    hl = (st.session_state.get("_dash_hl") or "").strip()
    if hl:
        with st.spinner("Running 7-stage ML analysis pipeline…"):
            result = run_analysis(hl, ticker)
            st.session_state["_result"] = result
            save_analysis(_uid, ticker, hl, result)
        st.success("Analysis complete.")
    else:
        st.warning("Please enter a headline first.")

# ── EMPTY STATE ───────────────────────────────────────────────────────────────
result = st.session_state.get("_result")
if result is None:
    st.markdown("""
        <div style="text-align:center;padding:3.5rem 1rem;color:#3D5268;">
            <div style="font-family:'Syne',sans-serif;font-size:1rem;
                        color:#2D4060;margin-bottom:.4rem;">◇ Ready to Analyze</div>
            <div style="font-size:.76rem;line-height:1.7;max-width:320px;margin:0 auto;
                        font-family:'Manrope',sans-serif;color:#3D5268;">
                Enter a headline above, pick a quick example,
                or click Analyze from the News Feed page.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── UNPACK RESULT ─────────────────────────────────────────────────────────────
pol     = result["polarity"]
raw_pol = result.get("raw_polarity", 0.0)
cat     = result["category"]
lbl     = result["label"]
conf    = result["confidence"]
rel     = result["relevance_score"]
cred    = result["credibility"]
evt     = result["event_type"]
is_rum  = result["is_rumour"]
macro_f = result.get("macro_factor", 1.0)
macro_d = result.get("macro_description", "")
sc      = sentiment_color(cat)
sk      = sentiment_badge_kind(cat)

# ── STAT ROW ──────────────────────────────────────────────────────────────────
_CM = {
    "STRONG_NEGATIVE":"#FF3D60","NEGATIVE":"#FF7D35",
    "NEUTRAL":"#7A92A8","POSITIVE":"#00E8A0","STRONG_POSITIVE":"#00E8A0",
}
c = _CM.get(cat, "#7A92A8")
st.markdown(
    stat_row(
        stat_box("Sentiment Score",    f"{pol:+.2f}",   lbl,                   c),
        stat_box("FinBERT Confidence", f"{conf:.0%}",   "Model certainty",     "#00C8F0"),
        stat_box("Relevance",          f"{rel:.0%}",    "Direct ticker news",  "#FFD060"),
        stat_box("Credibility",        f"{cred:.0%}",
                 "Rumour detected" if is_rum else "Confirmed source",
                 "#FF7D35" if is_rum else "#00E8A0"),
        stat_box("Ripple Entities",    str(len(result["ripple_tree"])),
                 "In corporate graph", "#9B6DFF"),
        stat_box("Event Type",         evt[:16],        f"×{result.get('event_multiplier',1):.2f}", "#FFD060"),
    ),
    unsafe_allow_html=True,
)

# ── RESULT TABS ───────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5, t6 = st.tabs(
    ["Sentiment", "Ripple Effect", "Historical", "Explainability", "Full Report", "📈 Market Chart"]
)

# ════════════════════════ TAB 1 — SENTIMENT ══════════════════════════════════
with t1:
    left, right = st.columns([3, 2])

    with left:
        st.markdown(f"""
            <div class="fi-card fi-card-accent">
                <div class="fi-title">Sentiment Impact Analysis</div>
                <div style="display:flex;align-items:center;gap:18px;margin-bottom:1rem;">
                    <div style="text-align:center;min-width:96px;">
                        <div style="font-family:'Syne',sans-serif;font-weight:800;
                                    font-size:2.8rem;color:{sc};line-height:1;">{pol:+.2f}</div>
                        <div style="font-size:.59rem;color:#3D5268;letter-spacing:.1em;
                                    text-transform:uppercase;margin-top:3px;font-family:'Manrope',sans-serif;">
                            Polarity Score</div>
                    </div>
                    <div style="flex:1;">
                        {polarity_bar(pol)}
                        <div style="display:flex;justify-content:space-between;margin-top:8px;">
                            {badge(lbl, sk)}
                            <span style="font-size:.65rem;color:#3D5268;font-family:'Manrope',sans-serif;">{evt}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="reason-box">{result["reason"]}</div>', unsafe_allow_html=True)

        if is_rum:
            st.warning("Rumour signals detected — sentiment confidence is dampened by credibility score.")
        if not result.get("is_relevant"):
            st.info(f"This headline may not be directly about {ticker} — relevance score adjusted.")

        jargon = result.get("jargon_detected", [])
        if jargon:
            st.markdown('<div class="fi-section">Financial Jargon Detected</div>', unsafe_allow_html=True)
            st.markdown(
                ' '.join(badge(j, "purple") for j in jargon),
                unsafe_allow_html=True,
            )

    with right:
        # Confidence breakdown
        st.markdown('<div class="fi-card"><div class="fi-title">Confidence Breakdown</div>',
                    unsafe_allow_html=True)
        hp = result.get("hist_prediction", {})
        bars = [
            ("FinBERT Score",    conf,                               "#00C8F0"),
            ("Relevance",        rel,                                "#FFD060"),
            ("Credibility",      cred,                               "#FF7D35" if is_rum else "#00E8A0"),
        ]
        if hp:
            bars.append(("Hist. Accuracy", hp.get("directional_acc", 0) / 100, "#9B6DFF"))
        for bl, val, bc in bars:
            st.markdown(mini_progress_bar(bl, val, bc), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Live price
        pd_data = get_price(ticker)
        if not pd_data.get("error"):
            st.markdown(live_price_card(ticker, pd_data), unsafe_allow_html=True)


# ════════════════════════ TAB 2 — RIPPLE EFFECT ══════════════════════════════
with t2:
    ripple = result.get("ripple_tree", [])
    if not ripple:
        st.info("No corporate hierarchy data available for this ticker.")
    else:
        n_pos = sum(1 for r in ripple if r["impact"] > 0.05)
        n_neg = sum(1 for r in ripple if r["impact"] < -0.05)
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;flex-wrap:wrap;">
                <span style="font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;">
                    Corporate Ripple Effect</span>
                {badge(f"{len(ripple)} entities", "neutral")}
                {badge(f"{n_pos} positive", "green") if n_pos else ""}
                {badge(f"{n_neg} negative", "red")   if n_neg else ""}
                <span style="font-size:.68rem;color:#3D5268;font-family:'Manrope',sans-serif;margin-left:4px;">
                    impact = ownership% × relationship_decay × depth_decay
                </span>
            </div>
        """, unsafe_allow_html=True)

        for node in ripple:
            st.markdown(ripple_node(node), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        names  = [n["name"][:30] for n in ripple]
        imps   = [n["impact"]    for n in ripple]
        colors = [impact_color(i) for i in imps]
        fig = go.Figure(go.Bar(
            x=imps, y=names, orientation="h",
            marker_color=colors,
            text=[f"{i:+.3f}" for i in imps],
            textposition="outside",
        ))
        fig.update_layout(
            paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
            font=dict(color="#7A92A8", size=10, family="Manrope"),
            xaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A", title="Impact Score"),
            yaxis=dict(gridcolor="#1A2535"),
            margin=dict(l=10, r=65, t=8, b=8),
            height=max(180, len(ripple) * 38),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════ TAB 3 — HISTORICAL ═════════════════════════════════
with t3:
    similar = result.get("similar_headlines", pd.DataFrame())
    hp      = result.get("hist_prediction", {})

    if similar.empty:
        st.info("No similar historical headlines found in the dataset.")
    else:
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:.9rem;">
                <span style="font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;">
                    Similar Historical Headlines</span>
                {badge(f"{len(similar)} matches", "neutral")}
            </div>
        """, unsafe_allow_html=True)

        for _, row in similar.iterrows():
            t3_val = row.get("t3_move_pct")
            sim    = row.get("similarity", 0)
            st.markdown(
                hist_row(
                    row.get("Headline", ""),
                    row.get("Date", "N/A"),
                    float(t3_val) if pd.notna(t3_val) else None,
                    float(sim),
                    row.get("EventType", "General"),
                ),
                unsafe_allow_html=True,
            )

        if hp:
            avg  = hp.get("avg_move", 0)
            rlo  = hp.get("range_low", avg)
            rhi  = hp.get("range_high", avg)
            dacc = hp.get("directional_acc", 0)
            n    = hp.get("sample_count", 0)
            pc   = "#00E8A0" if avg >= 0 else "#FF3D60"
            st.markdown(f"""
                <div class="pred-box">
                    <div class="pred-label">T+3 Prediction — {n} historical analogues</div>
                    <div class="pred-value" style="color:{pc};">
                        Likely range: {rlo:+.1f}% to {rhi:+.1f}%
                    </div>
                    <div style="font-size:.68rem;color:#3D5268;margin-top:4px;
                                font-family:'Manrope',sans-serif;">
                        Average: {avg:+.1f}% &nbsp;·&nbsp; Directional accuracy: {dacc:.0f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Scatter chart
        if "t3_move_pct" in similar.columns and "similarity" in similar.columns:
            fig2 = go.Figure()
            for _, row in similar.iterrows():
                t3v = float(row.get("t3_move_pct") or 0)
                sim = float(row.get("similarity") or 50)
                fc  = "#00E8A0" if t3v >= 0 else "#FF3D60"
                fig2.add_trace(go.Scatter(
                    x=[sim], y=[t3v], mode="markers+text",
                    marker=dict(size=14, color=fc, opacity=0.85,
                                line=dict(width=1, color="rgba(0,0,0,.3)")),
                    text=[row.get("Ticker", "")],
                    textposition="top center",
                    showlegend=False,
                ))
            fig2.add_hline(y=0, line_color="#22334A", line_dash="dot")
            fig2.update_layout(
                paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
                font=dict(color="#7A92A8", size=10, family="Manrope"),
                xaxis=dict(title="Similarity %", gridcolor="#1A2535"),
                yaxis=dict(title="Actual T+3 Move %", gridcolor="#1A2535",
                           zerolinecolor="#22334A"),
                margin=dict(l=10, r=10, t=10, b=30),
                height=300,
            )
            st.plotly_chart(fig2, use_container_width=True)


# ════════════════════════ TAB 4 — EXPLAINABILITY ═════════════════════════════
with t4:
    attrs = result.get("word_attributions", [])
    st.markdown("""
        <div style="font-size:.8rem;color:#7A92A8;margin-bottom:1rem;line-height:1.72;
                    font-family:'Manrope',sans-serif;">
            <strong style="color:#DDE6F0;">SHAP-style Word Attribution</strong> — Each word's
            contribution to the final sentiment score, based on a weighted financial lexicon.
            Green = bullish signal, Red = bearish signal.
        </div>
    """, unsafe_allow_html=True)

    if not attrs:
        st.info("No significant word attributions found.")
    else:
        max_c = max(abs(a["contribution"]) for a in attrs) or 1.0
        for a in attrs:
            st.markdown(attribution_bar(a["word"], a["contribution"], max_c),
                        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="fi-card">
            <div class="fi-title">Macro Context Injection · Stage 7</div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:.8rem;color:#7A92A8;font-family:'Manrope',sans-serif;">
                    {macro_d}</div>
                <div style="font-family:'Syne',sans-serif;font-weight:800;
                            font-size:1.2rem;color:#FFD060;">&times;{macro_f:.2f}</div>
            </div>
            <div style="font-size:.68rem;color:#3D5268;margin-top:6px;
                        font-family:'Manrope',sans-serif;">
                Base FinBERT:
                <span style="font-family:'JetBrains Mono',monospace;color:#DDE6F0;">{raw_pol:+.3f}</span>
                &nbsp;×&nbsp; macro factor &nbsp;→&nbsp;
                final: <span style="font-family:'JetBrains Mono',monospace;color:{sc};">{pol:+.3f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Pipeline summary
    st.markdown('<div class="fi-section">Pipeline Trace</div>', unsafe_allow_html=True)
    stages_html = [
        ("Stage 1 · NER",        ", ".join(result.get("detected_entities", [])) or "No entities"),
        ("Stage 2 · Event",      f"{evt} (×{result.get('event_multiplier',1):.2f})"),
        ("Stage 3 · FinBERT",    f"{raw_pol:+.3f} raw → {result.get('confidence',0):.0%} conf"),
        ("Stage 4 · Rumour",     f"{'Detected' if is_rum else 'Clean'} — credibility {cred:.0%}"),
        ("Stage 5 · SHAP",       f"{len(attrs)} attributed words"),
        ("Stage 6 · Historical", f"{len(result.get('similar_headlines', pd.DataFrame()))} matches"),
        ("Stage 7 · Macro",      f"×{macro_f:.2f} amplification"),
    ]
    rows_html = "".join(
        f'<tr style="border-bottom:1px solid #1A2535;">'
        f'<td style="padding:6px 0;color:#3D5268;font-family:\'JetBrains Mono\',monospace;'
        f'font-size:.68rem;width:38%;">{k}</td>'
        f'<td style="padding:6px 0;color:#DDE6F0;font-size:.75rem;'
        f'font-family:\'Manrope\',sans-serif;">{v}</td></tr>'
        for k, v in stages_html
    )
    st.markdown(
        f'<div class="fi-card"><table style="width:100%;border-collapse:collapse;">{rows_html}</table></div>',
        unsafe_allow_html=True,
    )


# ════════════════════════ TAB 5 — FULL REPORT ════════════════════════════════
with t5:
    ts = result.get("analyzed_at", "")[:19].replace("T", " ")
    rows_html = "".join(
        f'<tr style="border-bottom:1px solid #1A2535;">'
        f'<td style="padding:7px 0;color:#3D5268;font-family:\'JetBrains Mono\',monospace;'
        f'font-size:.67rem;width:38%;">{k}</td>'
        f'<td style="padding:7px 0;color:{vc};font-family:\'Manrope\',sans-serif;'
        f'font-size:.78rem;">{v}</td></tr>'
        for k, v, vc in [
            ("Headline",       result.get("headline",""),           "#DDE6F0"),
            ("Ticker",         result.get("ticker",""),             "#DDE6F0"),
            ("Sentiment",      lbl,                                  sc),
            ("Polarity",       f"{pol:+.3f}",                       sc),
            ("Raw FinBERT",    f"{raw_pol:+.3f}",                   "#DDE6F0"),
            ("Confidence",     f"{conf:.1%}",                        "#DDE6F0"),
            ("Relevance",      f"{rel:.1%}",                         "#DDE6F0"),
            ("Credibility",    f"{cred:.1%}",                        "#DDE6F0"),
            ("Event Type",     evt,                                  "#DDE6F0"),
            ("Event Multiplier",f"×{result.get('event_multiplier',1):.2f}", "#DDE6F0"),
            ("Rumour",         "Yes" if is_rum else "No",            "#FF7D35" if is_rum else "#00E8A0"),
            ("Macro Factor",   f"×{macro_f:.2f} — {macro_d}",       "#FFD060"),
            ("Entities",       ", ".join(result.get("detected_entities",[])) or "None", "#DDE6F0"),
            ("Jargon",         ", ".join(result.get("jargon_detected",[])) or "None",   "#9B6DFF"),
            ("Pipeline",       result.get("pipeline_version","v4"),  "#00C8F0"),
            ("Analyzed At",    ts,                                   "#DDE6F0"),
        ]
    )
    st.markdown(f"""
        <div class="fi-card">
            <div class="fi-title">Full Analysis Report
                <span style="font-family:'JetBrains Mono',monospace;font-size:.65rem;
                             color:#3D5268;margin-left:8px;">analyzed at {ts} UTC</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">{rows_html}</table>
        </div>
    """, unsafe_allow_html=True)


# ════════════════════════ TAB 6 — MARKET CHART ═══════════════════════════════
with t6:
    @st.cache_data(ttl=300)
    def _mkt_ohlcv(t, p):
        return get_ohlcv_with_indicators(t, p)

    @st.cache_data(ttl=300)
    def _mkt_indices():
        return get_index_prices()

    # Controls row
    mc1, mc2, mc3, mc4 = st.columns([2, 2, 2, 2])
    with mc1:
        mkt_ticker  = st.selectbox("Ticker", TICKERS, index=TICKERS.index(ticker) if ticker in TICKERS else 0, key="_mkt_t")
    with mc2:
        mkt_period  = st.selectbox("Period", list(PERIOD_OPTIONS.keys()), index=2, key="_mkt_p")
    with mc3:
        mkt_ctype   = st.radio("Chart", ["Candlestick", "Line"], horizontal=True, key="_mkt_ct")
    with mc4:
        mkt_ma      = st.toggle("Moving Averages", value=True,  key="_mkt_ma")
        mkt_vol     = st.toggle("Volume Bars",     value=True,  key="_mkt_vl")

    mkt_bb   = st.toggle("Bollinger Bands", value=False, key="_mkt_bb")

    df_mkt = _mkt_ohlcv(mkt_ticker, mkt_period)

    if df_mkt.empty:
        st.warning(f"No market data available for {mkt_ticker}. Try a different period.")
    else:
        # Price metrics
        pd2 = get_price(mkt_ticker)
        pm1, pm2, pm3, pm4 = st.columns(4)
        with pm1: st.metric("Price",         fmt_price(pd2))
        with pm2: st.metric("Day Change",     fmt_change(pd2))
        with pm3: st.metric("Period High",    f"{df_mkt['High'].max():,.2f}" if "High" in df_mkt.columns else "—")
        with pm4: st.metric("Period Low",     f"{df_mkt['Low'].min():,.2f}"  if "Low"  in df_mkt.columns else "—")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ── Main price chart ──────────────────────────────────────────────
        row_h = [0.68, 0.32] if mkt_vol else [1.0]
        n_rows = 2 if mkt_vol else 1
        fig_m = make_subplots(rows=n_rows, cols=1, shared_xaxes=True,
                              row_heights=row_h, vertical_spacing=0.03)

        if mkt_ctype == "Candlestick":
            fig_m.add_trace(go.Candlestick(
                x=df_mkt.index,
                open=df_mkt["Open"], high=df_mkt["High"],
                low=df_mkt["Low"],   close=df_mkt["Close"],
                name=mkt_ticker,
                increasing=dict(line=dict(color="#00E8A0"), fillcolor="rgba(0,232,160,.7)"),
                decreasing=dict(line=dict(color="#FF3D60"), fillcolor="rgba(255,61,96,.7)"),
            ), row=1, col=1)
        else:
            fig_m.add_trace(go.Scatter(
                x=df_mkt.index, y=df_mkt["Close"], mode="lines",
                name=mkt_ticker, line=dict(color="#00C8F0", width=2),
                fill="tozeroy", fillcolor="rgba(0,200,240,.05)",
            ), row=1, col=1)

        if mkt_ma:
            for col_n, color, dash in [("MA20","#FFD060","solid"),("MA50","#FF7D35","dash"),("MA200","#9B6DFF","dot")]:
                if col_n in df_mkt.columns:
                    fig_m.add_trace(go.Scatter(
                        x=df_mkt.index, y=df_mkt[col_n], mode="lines", name=col_n,
                        line=dict(color=color, width=1.2, dash=dash),
                    ), row=1, col=1)

        if mkt_bb and "BB_Upper" in df_mkt.columns:
            fig_m.add_trace(go.Scatter(
                x=df_mkt.index, y=df_mkt["BB_Upper"], mode="lines", name="BB Upper",
                line=dict(color="rgba(155,109,255,.5)", width=1, dash="dot"),
            ), row=1, col=1)
            fig_m.add_trace(go.Scatter(
                x=df_mkt.index, y=df_mkt["BB_Lower"], mode="lines", name="BB Lower",
                line=dict(color="rgba(155,109,255,.5)", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(155,109,255,.04)",
            ), row=1, col=1)

        if mkt_vol and "Volume" in df_mkt.columns:
            closes = df_mkt["Close"].tolist()
            opens  = df_mkt["Open"].tolist() if "Open" in df_mkt.columns else closes
            vol_c  = ["#00E8A0" if closes[i] >= opens[i] else "#FF3D60" for i in range(len(closes))]
            fig_m.add_trace(go.Bar(
                x=df_mkt.index, y=df_mkt["Volume"],
                name="Volume", marker_color=vol_c, marker_opacity=0.5,
            ), row=2, col=1)

        fig_m.update_layout(
            paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
            font=dict(color="#7A92A8", size=10, family="Manrope"),
            xaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A"),
            yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
            margin=dict(l=8, r=8, t=32, b=8),
            height=520 if mkt_vol else 400,
            title=dict(text=f"{mkt_ticker} · {mkt_ctype} · {mkt_period}",
                       font=dict(size=11, color="#DDE6F0", family="Syne")),
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": True})

        # ── RSI + MACD sub-panels ─────────────────────────────────────────
        si1, si2 = st.columns(2)
        with si1:
            if "RSI" in df_mkt.columns:
                rsi_v = float(df_mkt["RSI"].iloc[-1])
                rsi_l, rsi_c = rsi_signal(rsi_v)
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=df_mkt.index, y=df_mkt["RSI"], mode="lines",
                    line=dict(color="#00C8F0", width=1.6), name="RSI",
                ))
                fig_rsi.add_hline(y=70, line=dict(color="#FF3D60", width=1, dash="dash"))
                fig_rsi.add_hline(y=30, line=dict(color="#00E8A0", width=1, dash="dash"))
                fig_rsi.add_hrect(y0=70, y1=100, fillcolor="rgba(255,61,96,.04)", line_width=0)
                fig_rsi.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,232,160,.04)", line_width=0)
                fig_rsi.update_layout(
                    paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
                    font=dict(color="#7A92A8", size=9, family="Manrope"),
                    xaxis=dict(gridcolor="#1A2535"), yaxis=dict(range=[0,100], gridcolor="#1A2535"),
                    margin=dict(l=8,r=8,t=30,b=8), height=200, showlegend=False,
                    title=dict(text=f"RSI (14) — {rsi_v:.1f} · {rsi_l}",
                               font=dict(size=10, color=rsi_c, family="Syne")),
                )
                st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})

        with si2:
            if "MACD" in df_mkt.columns:
                fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                         row_heights=[0.6,0.4], vertical_spacing=0.04)
                fig_macd.add_trace(go.Scatter(x=df_mkt.index, y=df_mkt["MACD"],
                    mode="lines", name="MACD", line=dict(color="#00C8F0", width=1.5)), row=1, col=1)
                fig_macd.add_trace(go.Scatter(x=df_mkt.index, y=df_mkt["MACD_Signal"],
                    mode="lines", name="Signal", line=dict(color="#FF7D35", width=1.2, dash="dash")), row=1, col=1)
                hist_c = ["#00E8A0" if v >= 0 else "#FF3D60" for v in df_mkt["MACD_Hist"].tolist()]
                fig_macd.add_trace(go.Bar(x=df_mkt.index, y=df_mkt["MACD_Hist"],
                    name="Hist", marker_color=hist_c, marker_opacity=0.7), row=2, col=1)
                fig_macd.update_layout(
                    paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
                    font=dict(color="#7A92A8", size=9, family="Manrope"),
                    xaxis=dict(gridcolor="#1A2535"), yaxis=dict(gridcolor="#1A2535"),
                    margin=dict(l=8,r=8,t=30,b=8), height=200,
                    title=dict(text="MACD (12,26,9)",
                               font=dict(size=10, color="#DDE6F0", family="Syne")),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
                )
                st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})

        # ── Live index band ───────────────────────────────────────────────
        st.markdown('<div class="fi-section" style="margin-top:.5rem;">Global Indices</div>',
                    unsafe_allow_html=True)
        with st.spinner(""):
            idx = _mkt_indices()
        idx_cols = st.columns(len(MARKET_INDICES))
        for col, (name, d) in zip(idx_cols, idx.items()):
            if d.get("error"):
                with col:
                    st.markdown(f'<div style="text-align:center;font-size:.6rem;color:#3D5268;">{name}<br>N/A</div>',
                                unsafe_allow_html=True)
                continue
            pct   = d["chg_pct"]
            color = "#00E8A0" if pct >= 0 else "#FF3D60"
            arrow = "▲" if pct >= 0 else "▼"
            with col:
                st.markdown(f"""
                    <div style="text-align:center;background:#111927;border:1px solid #1A2535;
                                border-radius:8px;padding:.5rem .3rem;font-family:'Manrope',sans-serif;">
                        <div style="font-size:.52rem;color:#3D5268;letter-spacing:.1em;
                                    text-transform:uppercase;">{name}</div>
                        <div style="font-family:'Syne',sans-serif;font-size:.82rem;
                                    font-weight:700;color:#DDE6F0;">{d["price"]:,.0f}</div>
                        <div style="font-size:.65rem;color:{color};">{arrow}{abs(pct):.2f}%</div>
                    </div>
                """, unsafe_allow_html=True)
