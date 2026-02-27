"""
styles.py — Global CSS and HTML helpers.
SVG icons used throughout sidebar and UI — no emojis anywhere.
"""

import streamlit as st

# ── SVG ICON LIBRARY ──────────────────────────────────────────────────────────
# Clean 16x16 stroke icons for sidebar nav

ICONS = {
    "home": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>""",

    "dashboard": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>""",

    "news": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>
        <path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6z"/>
    </svg>""",

    "watchlist": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>""",

    "history": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="12 8 12 12 14 14"/>
        <path d="M3.05 11A9 9 0 1 1 4 17.7"/><polyline points="3 7 3 11 7 11"/>
    </svg>""",

    "settings": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>""",

    "logout": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
    </svg>""",
}


def icon(name: str, color: str = "currentColor") -> str:
    svg = ICONS.get(name, "")
    return svg.replace("currentColor", color)


# ── GLOBAL CSS ────────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg:      #07090D;
    --bg2:     #0B0F16;
    --bg3:     #0F1520;
    --panel:   #111927;
    --border:  #1A2535;
    --border2: #22334A;
    --text:    #DDE6F0;
    --text2:   #7A92A8;
    --text3:   #3D5268;
    --accent:  #00C8F0;
    --accent2: #0088AA;
    --green:   #00E8A0;
    --green2:  #00A86B;
    --red:     #FF3D60;
    --red2:    #AA1A35;
    --orange:  #FF7D35;
    --yellow:  #FFD060;
    --purple:  #9B6DFF;
}

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

[data-testid="stHeader"]       { display:none!important; }
[data-testid="stToolbar"]      { display:none!important; }
[data-testid="stStatusWidget"] { display:none!important; }
#MainMenu                      { display:none!important; }
footer                         { display:none!important; }
.stDeployButton                { display:none!important; }

.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1400px !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 220px !important;
}
[data-testid="stSidebarNav"] { display: none !important; }

/* Headings */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}
h1 { font-size: 1.5rem !important; letter-spacing: -0.01em; }
h2 { font-size: 1.1rem !important; }
h3 { font-size: 0.95rem !important; }

/* Metric cards */
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

/* Buttons */
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

/* Inputs */
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
.stTextInput label, .stTextArea label,
.stSelectbox label, .stMultiSelect label {
    font-size: 0.72rem !important;
    color: var(--text3) !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

/* Tabs */
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

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Expander */
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

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent2), var(--accent)) !important;
    border-radius: 4px !important;
}
.stProgress > div > div { background: var(--bg3) !important; border-radius: 4px !important; }

/* Alerts */
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

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

/* Custom card */
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

/* Badge */
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
.fi-badge-green  { background:rgba(0,232,160,0.1);  color:var(--green);  border:1px solid rgba(0,232,160,0.2); }
.fi-badge-red    { background:rgba(255,61,96,0.1);   color:var(--red);    border:1px solid rgba(255,61,96,0.2); }
.fi-badge-orange { background:rgba(255,125,53,0.1);  color:var(--orange); border:1px solid rgba(255,125,53,0.2); }
.fi-badge-accent { background:rgba(0,200,240,0.1);   color:var(--accent); border:1px solid rgba(0,200,240,0.2); }
.fi-badge-neutral{ background:rgba(122,146,168,0.1); color:var(--text2);  border:1px solid rgba(122,146,168,0.2); }
.fi-badge-yellow { background:rgba(255,208,96,0.1);  color:var(--yellow); border:1px solid rgba(255,208,96,0.2); }
.fi-badge-purple { background:rgba(155,109,255,0.1); color:var(--purple); border:1px solid rgba(155,109,255,0.2); }

/* Stat row */
.stat-row { display:flex; gap:12px; margin-bottom:1rem; flex-wrap:wrap; }
.stat-box {
    flex: 1; min-width: 110px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 0.85rem 1rem;
    position: relative;
    overflow: hidden;
}
.stat-box-label { font-size:0.65rem; color:var(--text3); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:5px; }
.stat-box-value { font-family:'Syne',sans-serif; font-weight:800; font-size:1.4rem; line-height:1; margin-bottom:3px; }
.stat-box-sub   { font-size:0.65rem; color:var(--text3); }
.stat-box-bar   { position:absolute; bottom:0; left:0; right:0; height:2px; }

/* Tree node */
.tree-node {
    display:flex; align-items:center; gap:10px;
    padding:0.65rem 0.85rem;
    border-radius:9px; border:1px solid var(--border);
    background:var(--bg3); margin-bottom:6px; transition:all 0.2s;
}
.tree-node:hover { border-color:var(--border2); }

/* History item */
.hist-item {
    display:flex; gap:10px; padding:0.85rem;
    border-radius:9px; border:1px solid var(--border);
    background:var(--bg3); margin-bottom:6px; transition:border-color 0.2s;
}
.hist-item:hover { border-color:var(--border2); }

/* Section label */
.section-label {
    font-size:0.68rem; color:var(--text3); letter-spacing:0.15em;
    text-transform:uppercase; margin-bottom:0.75rem;
    display:flex; align-items:center; gap:10px;
}
.section-label::after { content:''; flex:1; height:1px; background:var(--border); }

/* Divider */
.fi-divider { height:1px; background:var(--border); margin:1rem 0; }

/* Reason box */
.reason-box {
    background:var(--bg3); border:1px solid var(--border);
    border-left:3px solid var(--accent);
    border-radius:0 10px 10px 0;
    padding:0.9rem 1rem; font-size:0.82rem;
    color:var(--text2); line-height:1.75; margin-bottom:1rem;
}

/* Feed item */
.feed-item {
    padding:0.75rem 0; border-bottom:1px solid var(--border);
    cursor:pointer; transition:opacity 0.15s;
}
.feed-item:hover { opacity:0.75; }
.feed-item:last-child { border-bottom:none; }

/* Prediction box */
.pred-box {
    padding:0.9rem 1rem; background:var(--bg3);
    border-radius:10px; border:1px solid var(--border); margin-top:0.75rem;
}
.pred-label { font-size:0.68rem; color:var(--text3); letter-spacing:0.12em; text-transform:uppercase; margin-bottom:0.4rem; }
.pred-value { font-family:'Syne',sans-serif; font-weight:700; font-size:0.95rem; }

/* Sidebar nav link */
.nav-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border-radius: 8px;
    margin-bottom: 3px;
    cursor: pointer;
    text-decoration: none;
    color: var(--text2);
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    transition: all 0.15s;
    border: 1px solid transparent;
}
.nav-link:hover {
    background: rgba(255,255,255,0.04);
    color: var(--text);
    border-color: var(--border);
}
.nav-link.active {
    background: rgba(0,200,240,0.07);
    color: var(--accent);
    border-color: rgba(0,200,240,0.2);
}
.nav-link svg { flex-shrink: 0; opacity: 0.7; }
.nav-link.active svg { opacity: 1; }

.stSpinner > div { border-top-color: var(--accent) !important; }
</style>
"""


def inject_styles():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── HTML HELPERS ──────────────────────────────────────────────────────────────

def metric_card_html(label, value, sub, color="#00C8F0", bar_color="#00C8F0") -> str:
    return f"""
    <div class="stat-box">
        <div class="stat-box-label">{label}</div>
        <div class="stat-box-value" style="color:{color};">{value}</div>
        <div class="stat-box-sub">{sub}</div>
        <div class="stat-box-bar" style="background:linear-gradient(90deg,transparent,{bar_color});"></div>
    </div>
    """


def badge_html(text, kind="accent") -> str:
    return f'<span class="fi-badge fi-badge-{kind}">{text}</span>'


def sentiment_color(category: str) -> str:
    return {
        "STRONG_POSITIVE": "#00E8A0",
        "POSITIVE":        "#00E8A0",
        "NEUTRAL":         "#7A92A8",
        "NEGATIVE":        "#FF7D35",
        "STRONG_NEGATIVE": "#FF3D60",
    }.get(category, "#7A92A8")


def sentiment_badge_kind(category: str) -> str:
    return {
        "STRONG_POSITIVE": "green",
        "POSITIVE":        "green",
        "NEUTRAL":         "neutral",
        "NEGATIVE":        "orange",
        "STRONG_NEGATIVE": "red",
    }.get(category, "neutral")


def polarity_to_needle_pct(polarity: float) -> float:
    return round(((polarity + 1) / 2) * 100, 1)


def nav_link_html(icon_name: str, label: str, active: bool = False) -> str:
    color = "#00C8F0" if active else "#7A92A8"
    cls   = "nav-link active" if active else "nav-link"
    ico   = icon(icon_name, color)
    return f"""
    <div class="{cls}">
        {ico}
        <span>{label}</span>
    </div>
    """
