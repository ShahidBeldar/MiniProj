"""
styles.py — All CSS injected into Streamlit pages.
Call inject_styles() at the top of every page.
"""

import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --bg:       #07090D;
    --bg2:      #0B0F16;
    --bg3:      #0F1520;
    --panel:    #111927;
    --border:   #1A2535;
    --border2:  #22334A;
    --text:     #DDE6F0;
    --text2:    #7A92A8;
    --text3:    #3D5268;
    --accent:   #00C8F0;
    --accent2:  #0088AA;
    --green:    #00E8A0;
    --green2:   #00A86B;
    --red:      #FF3D60;
    --red2:     #AA1A35;
    --orange:   #FF7D35;
    --yellow:   #FFD060;
    --purple:   #9B6DFF;
}

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'DM Mono', monospace !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── HIDE DEFAULT CHROME ── */
[data-testid="stHeader"]          { display:none!important; }
[data-testid="stToolbar"]         { display:none!important; }
[data-testid="stStatusWidget"]    { display:none!important; }
#MainMenu                         { display:none!important; }
footer                            { display:none!important; }
.stDeployButton                   { display:none!important; }

/* ── MAIN CONTAINER ── */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1400px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 220px !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    font-size: 0.75rem !important;
    color: var(--text3) !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.sidebar-logo {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.3rem !important;
    color: var(--text) !important;
    padding: 1rem 0 0.5rem 0;
}
.sidebar-logo span { color: var(--accent) !important; }

/* ── PAGE TITLE ── */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}
h1 { font-size: 1.5rem !important; letter-spacing: -0.01em; }
h2 { font-size: 1.1rem !important; }
h3 { font-size: 0.95rem !important; }

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    color: var(--text3) !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 0 18px rgba(0,200,240,0.2) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 28px rgba(0,200,240,0.35) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text2) !important;
    border: 1px solid var(--border2) !important;
    box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--text2) !important;
    color: var(--text) !important;
    box-shadow: none !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,200,240,0.08) !important;
}
.stSelectbox > div > div > div { color: var(--text) !important; }

/* ── LABELS ── */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stMultiSelect label {
    font-size: 0.72rem !important;
    color: var(--text3) !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg3) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text3) !important;
    border-radius: 7px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.06em !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
}

/* ── DATAFRAME / TABLES ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
.stDataFrame th {
    background: var(--bg3) !important;
    color: var(--text3) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-family: 'DM Mono', monospace !important;
}
.stDataFrame td {
    font-size: 0.8rem !important;
    color: var(--text2) !important;
    background: var(--panel) !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent2), var(--accent)) !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: var(--bg3) !important;
    border-radius: 4px !important;
}

/* ── ALERTS ── */
.stAlert {
    border-radius: 10px !important;
    border: 1px solid !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stSuccess { border-color: var(--green2) !important; background: rgba(0,168,107,0.08) !important; }
.stError   { border-color: var(--red2)   !important; background: rgba(170,26,53,0.08) !important; }
.stWarning { border-color: var(--orange)  !important; background: rgba(255,125,53,0.08) !important; }
.stInfo    { border-color: var(--accent2) !important; background: rgba(0,136,170,0.08) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

/* ── CUSTOM CARD ── */
.fi-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.25rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}
.fi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,200,240,0.25), transparent);
}
.fi-card-title {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text);
    letter-spacing: 0.03em;
    margin-bottom: 0.75rem;
}

/* ── BADGE ── */
.fi-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}
.fi-badge-green  { background:rgba(0,232,160,0.1);  color:var(--green);  border:1px solid rgba(0,232,160,0.2);  }
.fi-badge-red    { background:rgba(255,61,96,0.1);   color:var(--red);    border:1px solid rgba(255,61,96,0.2);   }
.fi-badge-orange { background:rgba(255,125,53,0.1);  color:var(--orange); border:1px solid rgba(255,125,53,0.2);  }
.fi-badge-accent { background:rgba(0,200,240,0.1);   color:var(--accent); border:1px solid rgba(0,200,240,0.2);   }
.fi-badge-neutral{ background:rgba(122,146,168,0.1); color:var(--text2);  border:1px solid rgba(122,146,168,0.2); }
.fi-badge-yellow { background:rgba(255,208,96,0.1);  color:var(--yellow); border:1px solid rgba(255,208,96,0.2);  }
.fi-badge-purple { background:rgba(155,109,255,0.1); color:var(--purple); border:1px solid rgba(155,109,255,0.2); }

/* ── SENTIMENT COLORS ── */
.sn-strong-pos { color: var(--green)  !important; }
.sn-pos        { color: var(--green)  !important; }
.sn-neutral    { color: var(--text2)  !important; }
.sn-neg        { color: var(--orange) !important; }
.sn-strong-neg { color: var(--red)    !important; }

/* ── STAT ROW ── */
.stat-row {
    display: flex;
    gap: 12px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.stat-box {
    flex: 1;
    min-width: 110px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 0.85rem 1rem;
    position: relative;
    overflow: hidden;
}
.stat-box-label {
    font-size: 0.65rem;
    color: var(--text3);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.stat-box-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.4rem;
    line-height: 1;
    margin-bottom: 3px;
}
.stat-box-sub {
    font-size: 0.65rem;
    color: var(--text3);
}
.stat-box-bar {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
}

/* ── TREE NODE ── */
.tree-node {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.65rem 0.85rem;
    border-radius: 9px;
    border: 1px solid var(--border);
    background: var(--bg3);
    margin-bottom: 6px;
    transition: all 0.2s;
}
.tree-node:hover { border-color: var(--border2); }
.tree-node.parent { border-color: var(--accent); background: rgba(0,200,240,0.03); }
.tree-node.child  { margin-left: 24px; }
.tree-node.grandchild { margin-left: 48px; }

/* ── HISTORY ITEM ── */
.hist-item {
    display: flex;
    gap: 10px;
    padding: 0.85rem;
    border-radius: 9px;
    border: 1px solid var(--border);
    background: var(--bg3);
    margin-bottom: 6px;
    transition: border-color 0.2s;
}
.hist-item:hover { border-color: var(--border2); }

/* ── SECTION LABEL ── */
.section-label {
    font-size: 0.68rem;
    color: var(--text3);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── DIVIDER ── */
.fi-divider {
    height: 1px;
    background: var(--border);
    margin: 1rem 0;
}

/* ── REASON BOX ── */
.reason-box {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1rem;
    font-size: 0.82rem;
    color: var(--text2);
    line-height: 1.75;
    margin-bottom: 1rem;
}

/* ── FEED ITEM ── */
.feed-item {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    transition: opacity 0.15s;
}
.feed-item:hover { opacity: 0.75; }
.feed-item:last-child { border-bottom: none; }
.feed-source {
    font-size: 0.65rem;
    color: var(--text3);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.feed-headline {
    font-size: 0.82rem;
    color: var(--text2);
    line-height: 1.55;
    margin: 4px 0;
}

/* ── PREDICTION BOX ── */
.pred-box {
    padding: 0.9rem 1rem;
    background: var(--bg3);
    border-radius: 10px;
    border: 1px solid var(--border);
    margin-top: 0.75rem;
}
.pred-label {
    font-size: 0.68rem;
    color: var(--text3);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.pred-value {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.95rem;
}

/* ── SPINNER OVERRIDE ── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ── NAV LINK ACTIVE ── */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: rgba(0,200,240,0.08) !important;
    border-left: 3px solid var(--accent) !important;
    color: var(--accent) !important;
}
[data-testid="stSidebarNav"] a {
    color: var(--text2) !important;
    font-size: 0.85rem !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.75rem !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text) !important;
}
</style>
"""


METER_CSS = """
<style>
.meter-wrap {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}
.meter-track {
    height: 10px;
    border-radius: 5px;
    background: linear-gradient(90deg,
        #AA1133 0%, #FF3D60 20%, #FF7D35 35%,
        #444 50%,
        #00A86B 65%, #00E8A0 80%, #00FF88 100%
    );
    position: relative;
    margin: 0.5rem 0;
}
.meter-needle {
    position: absolute;
    top: -5px;
    width: 4px;
    height: 20px;
    background: #fff;
    border-radius: 2px;
    transform: translateX(-50%);
    box-shadow: 0 0 10px rgba(255,255,255,0.8);
    transition: left 1.2s cubic-bezier(0.34,1.56,0.64,1);
}
.meter-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.65rem;
    color: var(--text3);
    letter-spacing: 0.06em;
}
</style>
"""


def inject_styles():
    """Inject global CSS + meter CSS into current page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(METER_CSS, unsafe_allow_html=True)


def metric_card_html(label: str, value: str, sub: str, color: str = "#00C8F0", bar_color: str = "#00C8F0") -> str:
    """Return HTML for a custom stat card."""
    return f"""
    <div class="stat-box">
        <div class="stat-box-label">{label}</div>
        <div class="stat-box-value" style="color:{color};">{value}</div>
        <div class="stat-box-sub">{sub}</div>
        <div class="stat-box-bar" style="background:linear-gradient(90deg,transparent,{bar_color});"></div>
    </div>
    """


def badge_html(text: str, kind: str = "accent") -> str:
    """Return HTML for an inline badge."""
    return f'<span class="fi-badge fi-badge-{kind}">{text}</span>'


def sentiment_color(category: str) -> str:
    cmap = {
        "STRONG_POSITIVE": "#00E8A0",
        "POSITIVE":        "#00E8A0",
        "NEUTRAL":         "#7A92A8",
        "NEGATIVE":        "#FF7D35",
        "STRONG_NEGATIVE": "#FF3D60",
    }
    return cmap.get(category, "#7A92A8")


def sentiment_badge_kind(category: str) -> str:
    kmap = {
        "STRONG_POSITIVE": "green",
        "POSITIVE":        "green",
        "NEUTRAL":         "neutral",
        "NEGATIVE":        "orange",
        "STRONG_NEGATIVE": "red",
    }
    return kmap.get(category, "neutral")


def polarity_to_needle_pct(polarity: float) -> float:
    """Convert polarity [-1, 1] to needle CSS left % [0, 100]."""
    return round(((polarity + 1) / 2) * 100, 1)
