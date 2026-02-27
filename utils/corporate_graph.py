"""
corporate_graph.py — Corporate hierarchy engine.
Loads from JSON, optionally enriches via SEC EDGAR Exhibit 21.
Computes ripple-effect impact propagation across the tree.
"""

import json
import os
import networkx as nx
import streamlit as st
import requests
import pandas as pd
from typing import Optional


# ── LOAD HIERARCHY ────────────────────────────────────────────────────────────
def _hier_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "corporate_hierarchy.json"
    )

@st.cache_resource
def load_hierarchy() -> dict:
    with open(_hier_path(), "r") as f:
        return json.load(f)


# ── BUILD NETWORKX GRAPH ──────────────────────────────────────────────────────
@st.cache_data
def build_graph(ticker: str) -> nx.DiGraph:
    """
    Build a directed graph for the given ticker.
    Nodes: company names
    Edges: parent→child with ownership % and relationship type
    """
    hier = load_hierarchy()
    companies = hier.get("companies", {})

    if ticker not in companies:
        return nx.DiGraph()

    G = nx.DiGraph()
    root = companies[ticker]
    G.add_node(
        ticker,
        name=root["name"],
        exchange=root.get("exchange", ""),
        sector=root.get("sector", ""),
        depth=0,
        ownership=100,
        relationship="parent",
        is_root=True,
    )

    def add_children(parent_key: str, children: list, depth: int):
        for child in children:
            key = child["name"].replace(" ", "_")[:40]
            G.add_node(
                key,
                name=child["name"],
                sector=child.get("sector", ""),
                depth=depth,
                ownership=child.get("ownership", 100),
                relationship=child.get("relationship", "wholly_owned"),
                is_root=False,
            )
            G.add_edge(parent_key, key,
                       ownership=child.get("ownership", 100),
                       relationship=child.get("relationship", "wholly_owned"))

            if child.get("subsidiaries"):
                add_children(key, child["subsidiaries"], depth + 1)

    add_children(ticker, root.get("subsidiaries", []), 1)
    return G


# ── IMPACT PROPAGATION ────────────────────────────────────────────────────────
def compute_ripple(ticker: str, parent_polarity: float) -> list[dict]:
    """
    Given parent sentiment polarity [-1, 1], compute impact on each node
    using ownership weight × relationship decay × depth decay.

    Returns list of dicts sorted by abs(impact), parent first.
    """
    hier   = load_hierarchy()
    G      = build_graph(ticker)
    rel_dc = hier.get("relationship_types", {})
    dep_dc = hier.get("depth_decay", {})

    if G.number_of_nodes() == 0:
        return []

    results = []
    companies = hier.get("companies", {})
    root_data = companies.get(ticker, {})

    # Root node
    results.append({
        "name":         root_data.get("name", ticker),
        "ticker":       ticker,
        "sector":       root_data.get("sector", ""),
        "depth":        0,
        "ownership":    100,
        "relationship": "parent",
        "impact":       round(parent_polarity, 3),
        "decay_factor": 1.0,
        "is_root":      True,
        "description":  "Parent company — direct full impact",
    })

    def walk(parent_key: str, parent_impact: float, depth: int, path: list):
        for _, child_key, edge_data in G.out_edges(parent_key, data=True):
            node_data  = G.nodes[child_key]
            own_pct    = edge_data.get("ownership", 100)
            rel_type   = edge_data.get("relationship", "wholly_owned")

            rel_factor = rel_dc.get(rel_type, {}).get("decay", 0.8)
            dep_factor = float(dep_dc.get(str(depth), 0.3))
            own_factor = own_pct / 100.0

            decay  = rel_factor * dep_factor * own_factor
            impact = round(parent_impact * decay, 3)

            desc_parts = [
                rel_dc.get(rel_type, {}).get("label", rel_type),
                f"{own_pct}% stake",
                f"depth-{depth} decay",
            ]

            results.append({
                "name":         node_data["name"],
                "ticker":       None,
                "sector":       node_data.get("sector", ""),
                "depth":        depth,
                "ownership":    own_pct,
                "relationship": rel_type,
                "impact":       impact,
                "decay_factor": round(decay, 3),
                "is_root":      False,
                "description":  " · ".join(desc_parts),
                "path":         " → ".join(path + [node_data["name"]]),
            })

            walk(child_key, impact, depth + 1, path + [node_data["name"]])

    root_name = root_data.get("name", ticker)
    walk(ticker, parent_polarity, 1, [root_name])

    # Sort: root first, then by abs impact desc
    results.sort(key=lambda x: (-x["is_root"], -abs(x["impact"])))
    return results


# ── SEC EDGAR LIVE FETCH (best-effort) ───────────────────────────────────────
@st.cache_data(ttl=86400)   # 24h cache — filings don't change daily
def fetch_sec_subsidiaries(ticker: str) -> Optional[list[str]]:
    """
    Attempt to fetch subsidiary list from SEC EDGAR Exhibit 21.
    Returns list of subsidiary names or None on failure.
    This supplements the hardcoded data — it does NOT replace it.
    """
    try:
        # Step 1: Get CIK from ticker
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
            f"&dateRange=custom&startdt=2022-01-01&forms=10-K"
        )
        headers = {"User-Agent": "FinanceImpact research@financeimpact.io"}
        resp = requests.get(search_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return None

        cik = hits[0]["_source"].get("entity_id", "")
        if not cik:
            return None

        # Step 2: Get latest 10-K filing index
        filing_url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        resp2 = requests.get(filing_url, headers=headers, timeout=8)
        if resp2.status_code != 200:
            return None

        filings = resp2.json()
        recent  = filings.get("filings", {}).get("recent", {})
        forms   = recent.get("form", [])
        accs    = recent.get("accessionNumber", [])

        # Find latest 10-K
        acc_no = None
        for form, acc in zip(forms, accs):
            if form == "10-K":
                acc_no = acc.replace("-", "")
                break

        if not acc_no:
            return None

        # Step 3: Fetch Exhibit 21
        ex21_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
            f"/{acc_no}/ex21.htm"
        )
        resp3 = requests.get(ex21_url, headers=headers, timeout=10)
        if resp3.status_code != 200:
            return None

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp3.text, "html.parser")
        text = soup.get_text()
        # Parse subsidiary names (lines with "LLC", "Inc", "Corp", "Ltd")
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 5]
        subs  = [l for l in lines if any(
            kw in l for kw in ["LLC", "Inc.", "Corp.", "Ltd.", "GmbH", "S.A.", "Pvt"]
        )]
        return subs[:30] if subs else None

    except Exception:
        return None


@st.cache_data(ttl=86400)
def fetch_mca_subsidiaries(company_name: str) -> Optional[list[str]]:
    """
    Attempt to get Indian subsidiary info from MCA21 / NSE filings.
    Uses NSE's public company info endpoint as a lighter fallback.
    Returns list of subsidiary names or None.
    """
    try:
        # NSE public API — no auth required
        url = f"https://www.nseindia.com/api/corporate-affiliate?index={company_name.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return [item.get("companyName", "") for item in data if item.get("companyName")]
        return None
    except Exception:
        return None


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────
def impact_color(impact: float) -> str:
    if impact <= -0.5:  return "#FF3D60"
    if impact <= -0.15: return "#FF7D35"
    if impact < 0.15:   return "#7A92A8"
    if impact < 0.5:    return "#00E8A0"
    return "#00E8A0"

def impact_label(impact: float) -> str:
    if impact <= -0.5:  return "Strong Neg"
    if impact <= -0.15: return "Negative"
    if impact < 0.15:   return "Neutral"
    if impact < 0.5:    return "Positive"
    return "Strong Pos"

def relationship_icon(rel: str) -> str:
    icons = {
        "parent":             "🏢",
        "wholly_owned":       "🔗",
        "majority_owned":     "🔗",
        "joint_venture":      "🤝",
        "strategic_investment":"💼",
        "investment":         "📊",
        "division":           "🔧",
        "integrated":         "⚙️",
    }
    return icons.get(rel, "📌")

def depth_indent(depth: int) -> str:
    return "　" * depth   # CJK full-width space for clean indentation

def get_available_tickers() -> list[str]:
    hier = load_hierarchy()
    return list(hier.get("companies", {}).keys())
