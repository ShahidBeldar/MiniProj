"""
ui/theme.py — Global CSS injection + SVG icon library + shared Plotly theme.
FIX: .pol-track now has position:relative so .pol-thumb positions correctly.
Fonts: Syne (headings) · Manrope (body) · JetBrains Mono (data/mono)
"""
from __future__ import annotations
import streamlit as st


# ── SVG ICON LIBRARY ──────────────────────────────────────────────────────────

_ICONS: dict[str, str] = {
    "home": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/></svg>'
    ),
    "dashboard": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
    ),
    "news": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2z"/>'
        '<path d="M18 14h-8M15 18h-5M10 6h8v4h-8V6z"/></svg>'
    ),
    "watchlist": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="18" y1="20" x2="18" y2="10"/>'
        '<line x1="12" y1="20" x2="12" y2="4"/>'
        '<line x1="6"  y1="20" x2="6"  y2="14"/></svg>'
    ),
    "market": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
        '<polyline points="17 6 23 6 23 12"/></svg>'
    ),
    "history": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="12 8 12 12 14 14"/>'
        '<path d="M3.05 11A9 9 0 1 1 4 17.7"/>'
        '<polyline points="3 7 3 11 7 11"/></svg>'
    ),
    "settings": (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{c}" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06'
        'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65'
        ' 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 '
        '1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 '
        '4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 '
        '0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 '
        '1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 '
        '19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
        '</svg>'
    ),
}


def icon(name: str, color: str = "#7A92A8") -> str:
    return _ICONS.get(name, "").replace("{c}", color)


# ── SHARED PLOTLY CHART THEME ─────────────────────────────────────────────────

CHART_THEME: dict = dict(
    paper_bgcolor="#07090D",
    plot_bgcolor="#0F1520",
    font=dict(color="#7A92A8", size=10, family="Manrope, sans-serif"),
    xaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
               showgrid=True, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
               showgrid=True, tickfont=dict(size=9)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9, color="#7A92A8")),
    margin=dict(l=12, r=12, t=40, b=12),
    hoverlabel=dict(bgcolor="#111927", bordercolor="#22334A",
                    font_size=11, font_family="Manrope, sans-serif"),
)


# ── GLOBAL CSS ────────────────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Manrope:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ■■ TOKENS ■■ */
:root {
  --bg:#07090D; --bg2:#0B0F16; --bg3:#0F1520; --panel:#111927;
  --b1:#1A2535; --b2:#22334A; --b3:#2D4060;
  --t1:#DDE6F0; --t2:#7A92A8; --t3:#3D5268;
  --accent:#00C8F0; --acct2:#0085A8;
  --green:#00E8A0; --grn2:#00A86B;
  --red:#FF3D60;   --red2:#AA1133;
  --orange:#FF7D35; --yellow:#FFD060; --purple:#9B6DFF;
  --f-head:'Syne',sans-serif;
  --f-body:'Manrope',sans-serif;
  --f-mono:'JetBrains Mono',monospace;
  --radius:12px; --radius-sm:8px;
}

/* ■■ BASE ■■ */
html,body,[class*="css"] {
  font-family:var(--f-body)!important;
  background:var(--bg)!important;
  color:var(--t1)!important;
}

/* ■■ HIDE STREAMLIT CHROME ■■ */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
#MainMenu, footer, .stDeployButton { display:none!important; }

/* ■■ SIDEBAR ■■ */
[data-testid="stSidebarNav"] { display:none!important; }

.fi-sidebar-logo { padding:1.2rem 1rem .7rem; border-bottom:1px solid var(--b1); margin-bottom:.6rem; }
.fi-logo-text { font-family:'Syne',sans-serif; font-weight:800; font-size:1.28rem; color:var(--t1); letter-spacing:-.012em; line-height:1.1; }
.fi-logo-sub  { font-family:'Manrope',sans-serif; font-size:.54rem; color:var(--t3); letter-spacing:.22em; text-transform:uppercase; margin-top:4px; }

.fi-user-chip { display:flex; align-items:center; gap:9px; padding:8px 10px; background:var(--bg3); border-radius:10px; border:1px solid var(--b1); margin:0 .4rem .9rem; }
.fi-avatar    { width:28px; height:28px; border-radius:50%; flex-shrink:0; background:linear-gradient(135deg,#667eea,#764ba2); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; font-family:'Syne',sans-serif; color:#fff; }
.fi-username  { font-family:'Manrope',sans-serif; font-size:.8rem; font-weight:600; color:var(--t1); }
.fi-role      { font-size:.55rem; color:var(--t3); letter-spacing:.1em; font-family:'Manrope',sans-serif; }

.fi-nav      { display:flex; flex-direction:column; gap:2px; padding:0 .3rem; }
.fi-nav-link { display:flex!important; align-items:center!important; gap:10px!important; padding:9px 14px!important; border-radius:8px!important; font-family:'Manrope',sans-serif!important; font-size:.84rem!important; font-weight:500!important; color:var(--t2)!important; text-decoration:none!important; border:1px solid transparent!important; transition:background .15s,color .15s,border-color .15s!important; cursor:pointer!important; }
.fi-nav-link:hover { background:rgba(255,255,255,.04)!important; color:var(--t1)!important; border-color:var(--b1)!important; text-decoration:none!important; }
.fi-nav-icon { font-size:1rem; flex-shrink:0; }
.fi-nav-label { flex:1; }
.fi-sidebar-divider { height:1px; background:var(--b1); margin:.8rem .4rem .5rem; }

[data-testid="collapsedControl"] { display:flex!important; visibility:visible!important; background:var(--bg2)!important; border-right:1px solid var(--b1)!important; }
[data-testid="collapsedControl"] button { color:var(--t2)!important; background:transparent!important; border:none!important; box-shadow:none!important; }
[data-testid="collapsedControl"] button:hover { color:var(--accent)!important; transform:none!important; }

/* ■■ LAYOUT ■■ */
.block-container { padding:1.5rem 2.2rem!important; max-width:1520px!important; }
[data-testid="stSidebar"] { background:var(--bg2)!important; border-right:1px solid var(--b1)!important; min-width:220px!important; }
[data-testid="stSidebar"] > div:first-child { padding-top:0!important; }

/* ■■ TYPOGRAPHY ■■ */
h1,h2,h3,h4 { font-family:var(--f-head)!important; color:var(--t1)!important; font-weight:700!important; letter-spacing:-.015em!important; margin-bottom:.5rem!important; }
h1{font-size:1.55rem!important;} h2{font-size:1.1rem!important;} h3{font-size:.92rem!important;}
p,li,span,div { font-family:var(--f-body)!important; }
code,pre,[class*="mono"] { font-family:var(--f-mono)!important; }

/* ■■ METRICS ■■ */
[data-testid="metric-container"] { background:var(--panel)!important; border:1px solid var(--b1)!important; border-radius:var(--radius)!important; padding:.9rem 1rem!important; }
[data-testid="stMetricLabel"] { font-family:var(--f-body)!important; font-size:.63rem!important; font-weight:600!important; color:var(--t3)!important; letter-spacing:.12em!important; text-transform:uppercase!important; }
[data-testid="stMetricValue"] { font-family:var(--f-head)!important; font-weight:800!important; font-size:1.55rem!important; }

/* ■■ BUTTONS ■■ */
.stButton>button { background:linear-gradient(135deg,var(--accent),var(--acct2))!important; color:#000!important; border:none!important; border-radius:var(--radius-sm)!important; font-family:var(--f-body)!important; font-weight:600!important; font-size:.78rem!important; letter-spacing:.03em!important; padding:.52rem 1.2rem!important; transition:all .18s!important; box-shadow:0 0 16px rgba(0,200,240,.16)!important; }
.stButton>button:hover { transform:translateY(-1px)!important; box-shadow:0 4px 24px rgba(0,200,240,.30)!important; }
.stButton>button[kind="secondary"] { background:transparent!important; color:var(--t2)!important; border:1px solid var(--b2)!important; box-shadow:none!important; }
.stButton>button[kind="secondary"]:hover { border-color:var(--t2)!important; color:var(--t1)!important; transform:none!important; box-shadow:none!important; }

/* ■■ SIDEBAR BUTTONS ■■ */
[data-testid="stSidebar"] .stButton>button { text-align:left!important; justify-content:flex-start!important; font-family:var(--f-body)!important; font-size:.83rem!important; font-weight:500!important; letter-spacing:.005em!important; text-transform:none!important; border-radius:var(--radius-sm)!important; padding:9px 14px!important; margin-bottom:2px!important; width:100%!important; }
[data-testid="stSidebar"] .stButton>button[kind="secondary"] { background:transparent!important; color:var(--t2)!important; border:1px solid transparent!important; box-shadow:none!important; transform:none!important; }
[data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover { background:rgba(255,255,255,.03)!important; color:var(--t1)!important; border-color:var(--b1)!important; transform:none!important; box-shadow:none!important; }
[data-testid="stSidebar"] .stButton>button[kind="primary"] { background:rgba(0,200,240,.08)!important; color:var(--accent)!important; border:1px solid rgba(0,200,240,.20)!important; box-shadow:none!important; transform:none!important; }
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover { background:rgba(0,200,240,.12)!important; transform:none!important; box-shadow:none!important; }

/* ■■ INPUTS ■■ */
.stTextInput>div>div>input, .stTextArea>div>div>textarea { background:var(--bg3)!important; border:1px solid var(--b2)!important; border-radius:var(--radius-sm)!important; color:var(--t1)!important; font-family:var(--f-body)!important; font-size:.85rem!important; }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color:var(--accent)!important; outline:none!important; box-shadow:0 0 0 3px rgba(0,200,240,.10)!important; }
.stSelectbox>div>div { background:var(--bg3)!important; border:1px solid var(--b2)!important; border-radius:var(--radius-sm)!important; }
label,.stTextInput label,.stTextArea label,.stSelectbox label,.stToggle label { font-family:var(--f-body)!important; font-size:.63rem!important; font-weight:600!important; color:var(--t3)!important; letter-spacing:.1em!important; text-transform:uppercase!important; }

/* ■■ TABS ■■ */
.stTabs [data-baseweb="tab-list"] { background:var(--bg3)!important; border-radius:10px!important; padding:3px!important; gap:2px!important; border:1px solid var(--b1)!important; }
.stTabs [data-baseweb="tab"] { background:transparent!important; color:var(--t3)!important; border-radius:7px!important; font-family:var(--f-body)!important; font-size:.74rem!important; font-weight:500!important; border:none!important; padding:.4rem .95rem!important; }
.stTabs [aria-selected="true"] { background:var(--panel)!important; color:var(--t1)!important; border:1px solid var(--b2)!important; }

/* ■■ MISC ■■ */
.stAlert { border-radius:10px!important; font-family:var(--f-body)!important; font-size:.8rem!important; }
[data-testid="stExpander"] { background:var(--panel)!important; border:1px solid var(--b1)!important; border-radius:var(--radius)!important; }
[data-testid="stExpander"] summary { font-family:var(--f-body)!important; font-size:.84rem!important; font-weight:500!important; }
[data-testid="stForm"] { background:var(--bg3)!important; border:1px solid var(--b1)!important; border-radius:var(--radius)!important; }
[data-testid="stDownloadButton"]>button { background:transparent!important; color:var(--accent)!important; border:1px solid rgba(0,200,240,.25)!important; box-shadow:none!important; }
[data-testid="stDownloadButton"]>button:hover { background:rgba(0,200,240,.05)!important; transform:none!important; }
::-webkit-scrollbar{width:4px;height:4px;} ::-webkit-scrollbar-track{background:transparent;} ::-webkit-scrollbar-thumb{background:var(--b2);border-radius:2px;}

/* ■■ CARD COMPONENTS ■■ */
.fi-card { background:var(--panel); border:1px solid var(--b1); border-radius:var(--radius); padding:1.2rem 1.3rem; position:relative; overflow:hidden; margin-bottom:.7rem; }
.fi-card::before { content:''; position:absolute; top:0;left:0;right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(0,200,240,.15),transparent); }
.fi-card-accent { border-color:rgba(0,200,240,.22)!important; box-shadow:0 0 24px rgba(0,200,240,.06); }
.fi-card-green  { border-color:rgba(0,232,160,.20)!important; }
.fi-card-red    { border-color:rgba(255,61,96,.20)!important; }
.fi-title { font-family:var(--f-head); font-weight:600; font-size:.87rem; color:var(--t1); letter-spacing:.01em; margin-bottom:.75rem; }
.fi-divider { height:1px; background:var(--b1); margin:.7rem 0; }
.fi-section { font-family:var(--f-body); font-size:.61rem; font-weight:700; color:var(--t3); letter-spacing:.18em; text-transform:uppercase; display:flex; align-items:center; gap:10px; margin:.9rem 0 .55rem; }
.fi-section::after { content:''; flex:1; height:1px; background:var(--b1); }

/* ■■ STAT BOXES ■■ */
.stat-row { display:flex; gap:10px; margin-bottom:.9rem; flex-wrap:wrap; }
.stat-box { flex:1; min-width:100px; background:var(--panel); border:1px solid var(--b1); border-radius:var(--radius); padding:.8rem 1rem 1rem; position:relative; overflow:hidden; }
.stat-label { font-family:var(--f-body); font-size:.6rem; font-weight:600; color:var(--t3); letter-spacing:.14em; text-transform:uppercase; margin-bottom:4px; }
.stat-value { font-family:var(--f-head); font-weight:800; font-size:1.4rem; line-height:1; margin-bottom:3px; }
.stat-sub   { font-family:var(--f-body); font-size:.63rem; color:var(--t3); }
.stat-bar   { position:absolute; bottom:0; left:0; right:0; height:2px; }

/* ■■ BADGES ■■ */
.fi-badge      { display:inline-block; padding:2px 9px; border-radius:20px; font-family:var(--f-body); font-size:.61rem; font-weight:600; line-height:1.6; white-space:nowrap; }
.badge-green   { background:rgba(0,232,160,.1);   color:var(--green);  border:1px solid rgba(0,232,160,.25); }
.badge-red     { background:rgba(255,61,96,.1);   color:var(--red);    border:1px solid rgba(255,61,96,.25); }
.badge-orange  { background:rgba(255,125,53,.1);  color:var(--orange); border:1px solid rgba(255,125,53,.25); }
.badge-accent  { background:rgba(0,200,240,.1);   color:var(--accent); border:1px solid rgba(0,200,240,.25); }
.badge-neutral { background:rgba(122,146,168,.1); color:var(--t2);     border:1px solid rgba(122,146,168,.25); }
.badge-yellow  { background:rgba(255,208,96,.1);  color:var(--yellow); border:1px solid rgba(255,208,96,.25); }
.badge-purple  { background:rgba(155,109,255,.1); color:var(--purple); border:1px solid rgba(155,109,255,.25); }

/* ■■ TREE / HIST / REASON ■■ */
.tree-node { display:flex; align-items:center; gap:9px; padding:.58rem .9rem; border-radius:10px; border:1px solid var(--b1); background:var(--bg3); margin-bottom:5px; }
.tree-node:hover { border-color:var(--b2); }
.tree-node.root-node { border-color:rgba(0,200,240,.22); background:rgba(0,200,240,.03); }
.hist-item { display:flex; gap:9px; padding:.85rem; border-radius:10px; border:1px solid var(--b1); background:var(--bg3); margin-bottom:6px; }
.hist-item:hover { border-color:var(--b2); }
.reason-box { background:var(--bg3); border:1px solid var(--b1); border-left:3px solid var(--accent); border-radius:0 10px 10px 0; padding:.85rem 1rem; font-family:var(--f-body); font-size:.78rem; color:var(--t2); line-height:1.7; margin-bottom:.7rem; }
.pred-box   { padding:.9rem 1rem; background:var(--bg3); border-radius:10px; border:1px solid var(--b1); margin-top:.75rem; font-family:var(--f-body); }
.pred-label { font-size:.61rem; font-weight:700; color:var(--t3); letter-spacing:.12em; text-transform:uppercase; margin-bottom:4px; }
.pred-value { font-family:var(--f-head); font-weight:700; font-size:.92rem; }

/* ■■ NEWS CARD ■■ */
.news-card { background:var(--panel); border:1px solid var(--b1); border-radius:var(--radius); padding:12px 14px; margin-bottom:8px; transition:border-color .15s; }
.news-card:hover { border-color:var(--b2); }
.news-card.pos-card { border-left:3px solid var(--green); }
.news-card.neg-card { border-left:3px solid var(--red); }
.news-card.neu-card { border-left:3px solid var(--t3); }

/* ■■ POLARITY BAR ■■ */
/* FIX: position:relative added so the absolute thumb renders inside the track */
.pol-track {
  position: relative;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(90deg,#AA1133 0%,#FF3D60 20%,#FF7D35 33%,#2D4060 50%,#00A86B 67%,#00E8A0 80%,#00E8A0 100%);
}
.pol-thumb {
  position: absolute;
  top: -5px;
  width: 5px;
  height: 18px;
  background: #fff;
  border-radius: 3px;
  transform: translateX(-50%);
  box-shadow: 0 0 6px rgba(255,255,255,.6);
  pointer-events: none;
}

/* ■■ MARKET PAGE ■■ */
.ind-ticker-card { background:var(--panel); border:1px solid var(--b1); border-radius:var(--radius); padding:.9rem 1rem; transition:border-color .15s; }
.ind-ticker-card:hover { border-color:var(--b2); }
.ind-ticker-card.positive { border-top:2px solid var(--green); }
.ind-ticker-card.negative { border-top:2px solid var(--red); }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
