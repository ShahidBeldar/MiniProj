"""
ui/components.py — Reusable HTML component builders.
All functions return HTML strings for st.markdown(..., unsafe_allow_html=True).
"""
from __future__ import annotations


def badge(text: str, kind: str = "accent") -> str:
    return f'<span class="fi-badge badge-{kind}">{text}</span>'


def stat_box(label: str, value: str, sub: str, color: str) -> str:
    return (
        f'<div class="stat-box">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value" style="color:{color};">{value}</div>'
        f'<div class="stat-sub">{sub}</div>'
        f'<div class="stat-bar" style="background:linear-gradient(90deg,transparent,{color});"></div>'
        f'</div>'
    )


def stat_row(*boxes: str) -> str:
    return f'<div class="stat-row">{"".join(boxes)}</div>'


def polarity_bar(polarity: float) -> str:
    pct = round(((polarity + 1) / 2) * 100, 1)
    return f"""
<div>
  <div style="display:flex;justify-content:space-between;
              font-size:.59rem;color:#3D5268;margin-bottom:4px;font-family:'Manrope',sans-serif;">
    <span>-1.0 Strong Neg</span><span>0 Neutral</span><span>+1.0 Strong Pos</span>
  </div>
  <div class="pol-track">
    <div class="pol-thumb" style="left:{pct}%;"></div>
  </div>
</div>"""


def sentiment_color(cat: str) -> str:
    return {
        "STRONG_POSITIVE": "#00E8A0",
        "POSITIVE":        "#00E8A0",
        "NEUTRAL":         "#7A92A8",
        "NEGATIVE":        "#FF7D35",
        "STRONG_NEGATIVE": "#FF3D60",
    }.get(cat or "", "#7A92A8")


def sentiment_badge_kind(cat: str) -> str:
    return {
        "STRONG_POSITIVE": "green",
        "POSITIVE":        "green",
        "NEUTRAL":         "neutral",
        "NEGATIVE":        "orange",
        "STRONG_NEGATIVE": "red",
    }.get(cat or "", "neutral")


def mini_progress_bar(label: str, value: float, color: str) -> str:
    pct = max(0, min(100, int(value * 100)))
    return f"""
<div style="margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;
              font-size:.68rem;color:#7A92A8;margin-bottom:4px;">
    <span style="font-family:'Manrope',sans-serif;">{label}</span>
    <span style="color:{color};font-family:'Syne',sans-serif;font-weight:700;">{pct}%</span>
  </div>
  <div style="height:4px;background:#0F1520;border-radius:2px;overflow:hidden;">
    <div style="height:100%;width:{pct}%;background:{color};border-radius:2px;
                transition:width .4s ease;"></div>
  </div>
</div>"""


def page_header(title_html: str, subtitle: str = "") -> str:
    sub_html = (
        f'<p style="font-family:\'Manrope\',sans-serif;color:#3D5268;'
        f'font-size:.67rem;letter-spacing:.14em;text-transform:uppercase;'
        f'margin:4px 0 0;">{subtitle}</p>'
    ) if subtitle else ""
    return f"""
<div style="margin-bottom:1.6rem;">
  <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.6rem;
              letter-spacing:-.02em;color:#DDE6F0;line-height:1.1;">
    {title_html}
  </div>
  {sub_html}
</div>"""


def attribution_bar(word: str, contribution: float, max_c: float) -> str:
    w    = int(abs(contribution) / max_c * 100) if max_c else 0
    c    = "#00E8A0" if contribution > 0 else "#FF3D60"
    sign = "+" if contribution > 0 else "−"
    return f"""
<div style="display:flex;align-items:center;gap:10px;padding:7px 12px;
            border-radius:8px;background:#0F1520;border:1px solid #1A2535;margin-bottom:5px;">
  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.82rem;
              color:{c};min-width:16px;">{sign}</div>
  <div style="font-family:'Syne',sans-serif;font-size:.78rem;color:#DDE6F0;min-width:110px;">
    "{word}"
  </div>
  <div style="flex:1;height:5px;background:#07090D;border-radius:3px;overflow:hidden;">
    <div style="height:100%;width:{w}%;background:{c};border-radius:3px;"></div>
  </div>
  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.75rem;
              color:{c};min-width:42px;text-align:right;">{sign}{abs(contribution):.2f}</div>
</div>"""


def news_card(title: str, source: str, published: str, pol: float,
              tickers: str, is_rumour: bool, link: str) -> str:
    from core.feeds import sentiment_dot_color
    dc    = sentiment_dot_color(pol)
    side  = "pos-card" if pol > 0.1 else ("neg-card" if pol < -0.1 else "neu-card")
    chips = " ".join(
        f'<span class="fi-badge badge-accent">{t}</span>'
        for t in tickers.split(", ") if t and t != "GENERAL"
    )
    rumour_chip = '<span class="fi-badge badge-orange">Rumour</span>' if is_rumour else ""
    pol_sign = f"{pol:+.2f}"
    pol_kind = "green" if pol > 0.1 else ("red" if pol < -0.1 else "neutral")
    link_html = (f'<a href="{link}" target="_blank" '
                 f'style="font-size:.61rem;color:#3D5268;margin-left:auto;text-decoration:none;">'
                 f'Source →</a>') if link else ""
    return f"""
<div class="news-card {side}">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;">
    <span style="font-size:.62rem;color:#3D5268;letter-spacing:.07em;
                 text-transform:uppercase;font-family:'Manrope',sans-serif;">{source}</span>
    <span style="width:3px;height:3px;background:#3D5268;border-radius:50%;
                 display:inline-block;"></span>
    <span style="font-size:.61rem;color:#3D5268;font-family:'Manrope',sans-serif;">{published}</span>
    <span style="margin-left:auto;width:7px;height:7px;border-radius:50%;
                 background:{dc};box-shadow:0 0 6px {dc};flex-shrink:0;"></span>
  </div>
  <div style="font-size:.84rem;color:#DDE6F0;line-height:1.55;margin-bottom:7px;
              font-family:'Manrope',sans-serif;">{title}</div>
  <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;">
    {chips}
    <span class="fi-badge badge-{pol_kind}">{pol_sign}</span>
    {rumour_chip}
    {link_html}
  </div>
</div>"""


def ripple_node(node: dict) -> str:
    from core.graph import impact_color, impact_label, rel_tag
    depth = node["depth"]
    imp   = node["impact"]
    ic    = impact_color(imp)
    il    = impact_label(imp)
    indent = depth * 22
    root_cls = "root-node" if node["is_root"] else ""
    rel   = node.get("relationship", "")
    tag   = rel_tag(rel)
    dashed = "border-style:dashed;" if rel in ("joint_venture","strategic_investment","investment") else ""
    return f"""
<div class="tree-node {root_cls}" style="margin-left:{indent}px;{dashed}">
  <span style="font-family:'JetBrains Mono',monospace;font-size:.62rem;
               color:#3D5268;min-width:26px;text-align:center;background:#0F1520;
               border-radius:4px;padding:2px 4px;">{tag}</span>
  <div style="flex:1;min-width:0;">
    <div style="font-family:'Syne',sans-serif;font-weight:600;font-size:.8rem;
                color:#DDE6F0;">{node['name']}</div>
    <div style="font-size:.65rem;color:#3D5268;white-space:nowrap;overflow:hidden;
                text-overflow:ellipsis;font-family:'Manrope',sans-serif;">{node.get('description','')}</div>
  </div>
  <div style="text-align:right;flex-shrink:0;">
    <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.84rem;
                color:{ic};">{imp:+.3f}</div>
    <div style="font-size:.61rem;color:#3D5268;">{il} · {node['ownership']}%</div>
  </div>
</div>"""


def hist_row(hl: str, date: str, t3: float, sim: float, evt: str) -> str:
    t3_s = f"{t3:+.1f}%" if t3 is not None else "N/A"
    t3_c = "#00E8A0" if (t3 or 0) > 0 else "#FF3D60"
    return f"""
<div class="hist-item">
  <div style="font-family:'JetBrains Mono',monospace;font-size:.66rem;
              color:#3D5268;min-width:80px;padding-top:2px;">{date}</div>
  <div style="flex:1;">
    <div style="font-size:.8rem;color:#7A92A8;line-height:1.5;
                font-family:'Manrope',sans-serif;">{hl}</div>
    <div style="margin-top:5px;">{badge(evt or 'General','neutral')}</div>
  </div>
  <div style="text-align:right;flex-shrink:0;min-width:78px;">
    <div style="font-family:'Syne',sans-serif;font-weight:700;
                font-size:.88rem;color:{t3_c};">{t3_s}</div>
    <div style="font-size:.61rem;color:#3D5268;">T+3 · {sim:.0f}% sim</div>
  </div>
</div>"""


def live_price_card(ticker: str, price_d: dict) -> str:
    from core.stocks import fmt_price, fmt_change, chg_color
    p   = fmt_price(price_d)
    chg = fmt_change(price_d)
    cc  = chg_color(price_d)
    return f"""
<div class="fi-card" style="margin-top:.85rem;">
  <div class="fi-title" style="margin-bottom:.45rem;">{ticker} · Live Price</div>
  <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.6rem;
              color:#DDE6F0;line-height:1;">{p}</div>
  <div style="font-size:.78rem;color:{cc};margin-top:4px;
              font-family:'Manrope',sans-serif;">{chg} today</div>
</div>"""
