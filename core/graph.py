"""
core/graph.py — Corporate hierarchy + ripple effect propagation.
No Streamlit imports. Graph is loaded lazily and cached by callers.
Hierarchy JSON is seeded by core/seeder.py on first run.
"""
from __future__ import annotations
import json
import os
import networkx as nx


# ── HIERARCHY LOADING ─────────────────────────────────────────────────────────

def _hier_path() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, "data", "corporate_hierarchy.json")


_HIERARCHY_CACHE: dict | None = None


def get_hierarchy() -> dict:
    global _HIERARCHY_CACHE
    if _HIERARCHY_CACHE is None:
        try:
            with open(_hier_path()) as f:
                _HIERARCHY_CACHE = json.load(f)
        except Exception:
            # Fallback: attempt to seed on-the-fly
            try:
                from core.seeder import ensure_hierarchy
                ensure_hierarchy()
                with open(_hier_path()) as f:
                    _HIERARCHY_CACHE = json.load(f)
            except Exception:
                _HIERARCHY_CACHE = {
                    "companies": {},
                    "relationship_types": {},
                    "depth_decay": {},
                }
    return _HIERARCHY_CACHE


def get_tickers() -> list[str]:
    return list(get_hierarchy().get("companies", {}).keys())


# ── GRAPH CONSTRUCTION ────────────────────────────────────────────────────────

def build_graph(ticker: str) -> nx.DiGraph:
    """Build NetworkX DiGraph for a given ticker's subsidiary tree."""
    hier = get_hierarchy()
    companies = hier.get("companies", {})
    if ticker not in companies:
        return nx.DiGraph()

    G = nx.DiGraph()
    root = companies[ticker]
    G.add_node(
        ticker,
        name=root["name"],
        sector=root.get("sector", ""),
        depth=0,
        ownership=100,
        relationship="parent",
        is_root=True,
    )

    def _add(parent_key: str, children: list, depth: int):
        for ch in children:
            key = ch["name"].replace(" ", "_")[:40]
            G.add_node(
                key,
                name=ch["name"],
                sector=ch.get("sector", ""),
                depth=depth,
                ownership=ch.get("ownership", 100),
                relationship=ch.get("relationship", "wholly_owned"),
                is_root=False,
            )
            G.add_edge(
                parent_key, key,
                ownership=ch.get("ownership", 100),
                relationship=ch.get("relationship", "wholly_owned"),
            )
            if ch.get("subsidiaries"):
                _add(key, ch["subsidiaries"], depth + 1)

    _add(ticker, root.get("subsidiaries", []), 1)
    return G


# ── RIPPLE PROPAGATION ────────────────────────────────────────────────────────

def compute_ripple(ticker: str, polarity: float) -> list[dict]:
    """
    Propagate polarity through corporate tree.
    impact = parent_polarity × ownership_pct × relationship_decay × depth_decay
    """
    hier = get_hierarchy()
    G = build_graph(ticker)
    if G.number_of_nodes() == 0:
        return []

    rel_dc = hier.get("relationship_types", {})
    dep_dc = hier.get("depth_decay", {})
    cos = hier.get("companies", {})
    root = cos.get(ticker, {})

    results: list[dict] = [{
        "name":         root.get("name", ticker),
        "ticker":       ticker,
        "sector":       root.get("sector", ""),
        "depth":        0,
        "ownership":    100,
        "relationship": "parent",
        "impact":       round(polarity, 3),
        "decay_factor": 1.0,
        "is_root":      True,
        "description":  "Parent company — direct full impact",
    }]

    def _walk(pk: str, parent_impact: float, depth: int):
        for _, ck, ed in G.out_edges(pk, data=True):
            nd = G.nodes[ck]
            own   = ed.get("ownership", 100)
            rel   = ed.get("relationship", "wholly_owned")
            rel_f = rel_dc.get(rel, {}).get("decay", 0.8)
            dep_f = float(dep_dc.get(str(depth), 0.3))
            own_f = own / 100.0
            decay  = rel_f * dep_f * own_f
            impact = round(parent_impact * decay, 3)
            results.append({
                "name":         nd["name"],
                "ticker":       None,
                "sector":       nd.get("sector", ""),
                "depth":        depth,
                "ownership":    own,
                "relationship": rel,
                "impact":       impact,
                "decay_factor": round(decay, 3),
                "is_root":      False,
                "description": (
                    f"{rel_dc.get(rel, {}).get('label', rel)} · "
                    f"{own}% stake · depth-{depth} decay ×{dep_f:.2f}"
                ),
            })
            _walk(ck, impact, depth + 1)

    _walk(ticker, polarity, 1)
    results.sort(key=lambda x: (-x["is_root"], -abs(x["impact"])))
    return results


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────

def impact_color(v: float) -> str:
    if v <= -0.5:  return "#FF3D60"
    if v <= -0.15: return "#FF7D35"
    if v <  0.15:  return "#7A92A8"
    if v <  0.5:   return "#7EC882"
    return "#00E8A0"


def impact_label(v: float) -> str:
    if v <= -0.5:  return "Strong Neg"
    if v <= -0.15: return "Negative"
    if v <  0.15:  return "Neutral"
    if v <  0.5:   return "Positive"
    return "Strong Pos"


def rel_tag(rel: str) -> str:
    return {
        "parent":               "P",
        "wholly_owned":         "W",
        "majority_owned":       "M",
        "joint_venture":        "JV",
        "strategic_investment": "SI",
        "investment":           "I",
        "division":             "D",
        "integrated":           "G",
    }.get(rel, "?")
