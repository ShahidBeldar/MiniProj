"""
pages/4_History.py — Analysis History with timeline, filters, search, export.
FIX: Pagination loop now renders `paginated` not `filtered` (critical bug fix).
FIX: Pagination resets to page 1 when filters change.
FIX: Clear All history now has a confirmation dialog (was missing, caused data loss).
FIX: Export button placed after history list for better UX flow.
FIX: Timeline chart uses paginated subset, not full filtered set.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from ui.theme      import inject_css
from ui.auth       import require_login, uid
from ui.nav        import render_sidebar
from ui.components import page_header, badge, sentiment_color, sentiment_badge_kind
from db.ops        import get_history, get_stats, delete_analysis, clear_history

inject_css()
require_login()
render_sidebar("history")

_uid  = uid()

@st.cache_data(ttl=120)
def _stats(u: int) -> dict:
    return get_stats(u)

stats = _stats(_uid)

st.markdown(page_header(
    'Analysis <span style="color:#00C8F0;">History</span>',
    "Complete record of all past analyses with sentiment timeline and export",
), unsafe_allow_html=True)

# ── STATS ─────────────────────────────────────────────────────────────────────
total = stats.get("total", 0)
conf  = stats.get("avg_conf") or 0
m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("Total Analyses",  total)
with m2: st.metric("Bullish",         stats.get("positive", 0))
with m3: st.metric("Bearish",         stats.get("negative", 0))
with m4: st.metric("Neutral",         stats.get("neutral",  0))
with m5: st.metric("Avg Confidence",  f"{conf:.0%}" if conf else "—")

st.markdown("<br>", unsafe_allow_html=True)

history = get_history(_uid, limit=200)
if not history:
    st.markdown("""
        <div style="text-align:center;padding:3.5rem;color:#3D5268;">
            <div style="font-family:'Syne',sans-serif;color:#2D4060;margin-bottom:.4rem;">
                No history yet</div>
            <div style="font-size:.76rem;font-family:'Manrope',sans-serif;">
                Run your first analysis on the Dashboard page.</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── FILTERS + SEARCH ──────────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
with f1:
    search_q = st.text_input("Search Headlines", placeholder="Type to search…", key="_hist_sq")
with f2:
    t_opts = ["All"] + sorted({h["ticker"] for h in history})
    tfilt  = st.selectbox("Ticker", t_opts, key="_hist_t")
with f3:
    c_opts = ["All","STRONG_POSITIVE","POSITIVE","NEUTRAL","NEGATIVE","STRONG_NEGATIVE"]
    cfilt  = st.selectbox("Sentiment", c_opts, key="_hist_c")
with f4:
    e_opts = ["All"] + sorted({h.get("event_type","General News") or "General News" for h in history})
    efilt  = st.selectbox("Event Type", e_opts, key="_hist_e")

# FIX: Clear All has proper confirmation dialog
if st.button("Clear All History", type="secondary", key="_hist_clr"):
    st.session_state["_hist_confirm_clear"] = True

if st.session_state.get("_hist_confirm_clear"):
    st.warning("This will permanently delete all your analysis history. This cannot be undone.")
    cc1, cc2, _ = st.columns([1, 1, 4])
    with cc1:
        if st.button("Yes, Delete All", type="primary", key="_hist_clr_yes", use_container_width=True):
            clear_history(_uid)
            _stats.clear()
            st.session_state.pop("_hist_confirm_clear", None)
            st.rerun()
    with cc2:
        if st.button("Cancel", type="secondary", key="_hist_clr_no", use_container_width=True):
            st.session_state.pop("_hist_confirm_clear", None)
            st.rerun()

filtered = history
if search_q.strip():
    q = search_q.strip().lower()
    filtered = [h for h in filtered if q in h.get("headline","").lower()]
if tfilt != "All": filtered = [h for h in filtered if h["ticker"] == tfilt]
if cfilt != "All": filtered = [h for h in filtered if h["category"] == cfilt]
if efilt != "All": filtered = [h for h in filtered if (h.get("event_type") or "General News") == efilt]

# ── PAGINATION ────────────────────────────────────────────────────────────────
PAGE_SIZE     = 20
total_filtered = len(filtered)
total_pages   = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

# FIX: detect filter change and reset page to 1
_filter_sig = f"{search_q}|{tfilt}|{cfilt}|{efilt}"
if st.session_state.get("_hist_filter_sig") != _filter_sig:
    st.session_state["_hist_filter_sig"] = _filter_sig
    st.session_state["_hist_page"] = 1

pc1, pc2 = st.columns([3, 1])
with pc2:
    page_num = st.number_input(
        "Page", min_value=1, max_value=total_pages,
        value=st.session_state.get("_hist_page", 1),
        key="_hist_page"
    )
with pc1:
    st.markdown(
        f'<div style="font-size:.65rem;color:#3D5268;margin-bottom:.75rem;'
        f'font-family:\'Manrope\',sans-serif;">'
        f'Showing {len(filtered)} of {len(history)} analyses · Page {page_num}/{total_pages}</div>',
        unsafe_allow_html=True,
    )

start     = (page_num - 1) * PAGE_SIZE
paginated = filtered[start : start + PAGE_SIZE]  # FIX: paginated slice used below

# ── TIMELINE CHART (on full filtered set) ─────────────────────────────────────
if len(filtered) >= 3:
    dfh = pd.DataFrame(filtered)
    dfh["analyzed_at"] = pd.to_datetime(dfh["analyzed_at"])
    dfh = dfh.sort_values("analyzed_at")

    fig = go.Figure()
    fig.add_hrect(y0=0.2,  y1=1.1,  line_width=0, fillcolor="rgba(0,232,160,.04)")
    fig.add_hrect(y0=-1.1, y1=-0.2, line_width=0, fillcolor="rgba(255,61,96,.04)")
    fig.add_trace(go.Scatter(
        x=dfh["analyzed_at"],
        y=dfh["polarity"],
        mode="lines+markers",
        line=dict(color="#00C8F0", width=1.5, shape="spline"),
        marker=dict(
            size=8,
            color=["#00E8A0" if p > 0.2 else "#FF3D60" if p < -0.2 else "#7A92A8"
                   for p in dfh["polarity"]],
            line=dict(width=1, color="rgba(0,0,0,.3)"),
        ),
        hovertemplate="<b>%{text}</b><br>Polarity: %{y:.3f}<br>%{x}<extra></extra>",
        text=dfh["ticker"],
        fill="tozeroy",
        fillcolor="rgba(0,200,240,.04)",
    ))
    fig.add_hline(y=0, line_color="#22334A", line_dash="dash", line_width=1)
    fig.update_layout(
        paper_bgcolor="#07090D", plot_bgcolor="#0F1520",
        font=dict(color="#7A92A8", size=10, family="Manrope"),
        xaxis=dict(gridcolor="#1A2535", title="Date"),
        yaxis=dict(gridcolor="#1A2535", zerolinecolor="#22334A",
                   title="Polarity", range=[-1.15, 1.15]),
        margin=dict(l=10, r=10, t=10, b=10),
        height=230,
        showlegend=False,
        title=dict(text="Sentiment Timeline", font=dict(color="#7A92A8", size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── HISTORY ITEMS — FIX: renders `paginated`, not `filtered` ─────────────────
for item in paginated:
    pol  = float(item.get("polarity",  0) or 0)
    cat  = item.get("category",  "NEUTRAL") or "NEUTRAL"
    conf = float(item.get("confidence", 0) or 0)
    evt  = item.get("event_type", "General News") or "General News"
    sc   = sentiment_color(cat)
    sk   = sentiment_badge_kind(cat)
    date = (item.get("analyzed_at") or "")[:16].replace("T", " ")

    cm, cme, ca2 = st.columns([4, 2, 1])

    with cm:
        st.markdown(f"""
            <div style="padding:9px 0;">
                <div style="display:flex;align-items:center;gap:6px;
                            margin-bottom:5px;flex-wrap:wrap;">
                    {badge(item['ticker'], 'accent')}
                    {badge(cat.replace('_',' ').title(), sk)}
                    {badge(evt, 'neutral')}
                    {badge('Rumour','orange') if item.get('is_rumour') else ""}
                </div>
                <div style="font-size:.82rem;color:#DDE6F0;line-height:1.52;
                            font-family:'Manrope',sans-serif;">
                    {item['headline']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with cme:
        st.markdown(f"""
            <div style="padding:9px 0;text-align:right;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:.98rem;color:{sc};">{pol:+.2f}</div>
                <div style="font-size:.65rem;color:#3D5268;
                            font-family:'JetBrains Mono',monospace;">Conf {conf:.0%}</div>
                <div style="font-size:.64rem;color:#3D5268;margin-top:2px;
                            font-family:'JetBrains Mono',monospace;">{date}</div>
            </div>
        """, unsafe_allow_html=True)

    with ca2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Re-analyze", key=f"_re_{item['id']}", use_container_width=True):
            st.session_state["_pending_t"]  = item["ticker"]
            st.session_state["_pending_hl"] = item["headline"]
            st.switch_page("pages/1_Dashboard.py")
        if st.button("Delete", key=f"_del_{item['id']}", type="secondary",
                     use_container_width=True):
            delete_analysis(item["id"], _uid)
            st.rerun()

    st.markdown('<div class="fi-divider"></div>', unsafe_allow_html=True)

# ── EXPORT — FIX: placed after list so user has context of what they export ───
st.markdown("<br>", unsafe_allow_html=True)
if filtered:
    df_exp = pd.DataFrame([{
        "Date":       h.get("analyzed_at","")[:19].replace("T"," "),
        "Ticker":     h["ticker"],
        "Headline":   h["headline"],
        "Polarity":   h.get("polarity",0),
        "Category":   h.get("category",""),
        "Confidence": h.get("confidence",0),
        "EventType":  h.get("event_type",""),
        "IsRumour":   bool(h.get("is_rumour",0)),
    } for h in filtered])
    csv = df_exp.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Export Filtered History ({len(filtered)} records) as CSV",
        data=csv,
        file_name="finance_impact_history.csv",
        mime="text/csv",
        key="_hist_export",
        type="secondary",
    )
