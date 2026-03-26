"""
core/seeder.py — Generates:
  data/news.csv               — 200+ historical headlines for similarity search
  data/corporate_hierarchy.json — NetworkX graph source for ripple propagation
No Streamlit imports.
"""
from __future__ import annotations
import json
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ── CORPORATE HIERARCHY ───────────────────────────────────────────────────────

_HIERARCHY: dict = {
    "companies": {
        "TSLA": {
            "name": "Tesla, Inc.",
            "sector": "Automotive / Energy",
            "subsidiaries": [
                {
                    "name": "Tesla Energy",
                    "sector": "Energy Storage",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [
                        {"name": "Megapack Manufacturing", "sector": "Manufacturing",
                         "ownership": 100, "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "SolarCity",
                    "sector": "Solar Energy",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Giga Nevada (Panasonic JV)",
                    "sector": "Battery Manufacturing",
                    "ownership": 50,
                    "relationship": "joint_venture",
                    "subsidiaries": [],
                },
                {
                    "name": "Tesla Insurance",
                    "sector": "Financial Services",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Autopilot / FSD Division",
                    "sector": "AI / Software",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
            ],
        },
        "AAPL": {
            "name": "Apple Inc.",
            "sector": "Technology",
            "subsidiaries": [
                {
                    "name": "Apple Services",
                    "sector": "Software & Services",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [
                        {"name": "Apple TV+", "sector": "Streaming", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                        {"name": "Apple Arcade", "sector": "Gaming", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "Beats Electronics",
                    "sector": "Consumer Electronics",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Shazam",
                    "sector": "Music Recognition",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Apple Pay / Wallet",
                    "sector": "FinTech",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
            ],
        },
        "GOOGL": {
            "name": "Alphabet Inc.",
            "sector": "Technology",
            "subsidiaries": [
                {
                    "name": "Google LLC",
                    "sector": "Search / Advertising",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [
                        {"name": "YouTube", "sector": "Video / Media", "ownership": 100,
                         "relationship": "wholly_owned", "subsidiaries": []},
                        {"name": "Google Cloud", "sector": "Cloud Computing", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "Waymo",
                    "sector": "Autonomous Vehicles",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "DeepMind",
                    "sector": "AI Research",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Verily Life Sciences",
                    "sector": "Healthcare Tech",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Wing (Drone Delivery)",
                    "sector": "Logistics / Drones",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
        "MSFT": {
            "name": "Microsoft Corp.",
            "sector": "Technology",
            "subsidiaries": [
                {
                    "name": "Microsoft Azure",
                    "sector": "Cloud Computing",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "LinkedIn",
                    "sector": "Professional Networking",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "GitHub",
                    "sector": "Developer Tools",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Activision Blizzard",
                    "sector": "Gaming",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [
                        {"name": "Call of Duty Studio", "sector": "Game Development", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "Xbox Game Studios",
                    "sector": "Gaming",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
            ],
        },
        "NVDA": {
            "name": "NVIDIA Corp.",
            "sector": "Semiconductors / AI",
            "subsidiaries": [
                {
                    "name": "Mellanox Technologies",
                    "sector": "Networking",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "GeForce / Gaming Division",
                    "sector": "Consumer GPUs",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "CUDA Platform",
                    "sector": "AI / HPC Software",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "NVIDIA AI Enterprise",
                    "sector": "Enterprise Software",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
            ],
        },
        "AMZN": {
            "name": "Amazon.com Inc.",
            "sector": "E-Commerce / Cloud",
            "subsidiaries": [
                {
                    "name": "Amazon Web Services (AWS)",
                    "sector": "Cloud Computing",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "Prime Video",
                    "sector": "Streaming",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "Whole Foods Market",
                    "sector": "Grocery Retail",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Twitch Interactive",
                    "sector": "Live Streaming / Gaming",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Ring (Smart Home)",
                    "sector": "Smart Home Devices",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Zappos",
                    "sector": "Online Retail",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
        "RELIANCE": {
            "name": "Reliance Industries Ltd.",
            "sector": "Conglomerate",
            "subsidiaries": [
                {
                    "name": "Jio Platforms",
                    "sector": "Telecom / Digital",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [
                        {"name": "JioMart", "sector": "E-Commerce", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                        {"name": "JioCinema", "sector": "OTT Streaming", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "Reliance Retail",
                    "sector": "Retail",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [
                        {"name": "AJIO", "sector": "Fashion E-Commerce", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                        {"name": "Reliance Fresh", "sector": "Grocery", "ownership": 100,
                         "relationship": "division", "subsidiaries": []},
                    ],
                },
                {
                    "name": "Reliance Petrochemicals",
                    "sector": "Petrochemicals",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "Reliance New Energy",
                    "sector": "Renewable Energy",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
        "TCS": {
            "name": "Tata Consultancy Services",
            "sector": "IT Services",
            "subsidiaries": [
                {
                    "name": "TCS BaNCS",
                    "sector": "Banking Software",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "TCS iON",
                    "sector": "EdTech / Assessment",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
                {
                    "name": "Diligenta",
                    "sector": "Insurance BPO",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
        "INFY": {
            "name": "Infosys Ltd.",
            "sector": "IT Services",
            "subsidiaries": [
                {
                    "name": "EdgeVerve Systems",
                    "sector": "AI / Automation",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Infosys BPM",
                    "sector": "Business Process Mgmt",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Skava",
                    "sector": "Digital Commerce",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
        "WIPRO": {
            "name": "Wipro Ltd.",
            "sector": "IT Services",
            "subsidiaries": [
                {
                    "name": "Capco",
                    "sector": "Financial Consulting",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Designit",
                    "sector": "Design / Innovation",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "Wipro Digital",
                    "sector": "Digital Transformation",
                    "ownership": 100,
                    "relationship": "division",
                    "subsidiaries": [],
                },
            ],
        },
        "HDFCBANK": {
            "name": "HDFC Bank Ltd.",
            "sector": "Banking / Financial Services",
            "subsidiaries": [
                {
                    "name": "HDFC Life Insurance",
                    "sector": "Life Insurance",
                    "ownership": 50,
                    "relationship": "majority_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "HDFC Securities",
                    "sector": "Stock Broking",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "HDFC AMC",
                    "sector": "Asset Management",
                    "ownership": 52,
                    "relationship": "majority_owned",
                    "subsidiaries": [],
                },
                {
                    "name": "HDFC Credila",
                    "sector": "Education Loans",
                    "ownership": 100,
                    "relationship": "wholly_owned",
                    "subsidiaries": [],
                },
            ],
        },
    },
    "relationship_types": {
        "wholly_owned":         {"label": "Wholly Owned",        "decay": 0.90},
        "majority_owned":       {"label": "Majority Owned",       "decay": 0.65},
        "joint_venture":        {"label": "Joint Venture",        "decay": 0.45},
        "strategic_investment": {"label": "Strategic Investment", "decay": 0.25},
        "investment":           {"label": "Investment",           "decay": 0.15},
        "division":             {"label": "Division",             "decay": 0.85},
        "integrated":           {"label": "Integrated",           "decay": 0.80},
        "parent":               {"label": "Parent",               "decay": 1.00},
    },
    "depth_decay": {
        "1": 0.70,
        "2": 0.40,
        "3": 0.20,
    },
}


def ensure_hierarchy() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, "data", "corporate_hierarchy.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(_HIERARCHY, f, indent=2)
    return path


# ── NEWS CSV ──────────────────────────────────────────────────────────────────

_BASE_ROWS = [
    # (Ticker, Headline, Sentiment, T+3_move, EventType)
    ("TSLA","Tesla faces record $4.2B EU fine over autopilot safety violations","STRONG_NEGATIVE",-4.3,"Regulatory/Legal"),
    ("TSLA","Tesla recalls 485000 vehicles over rear camera defects","NEGATIVE",-2.8,"Regulatory/Legal"),
    ("TSLA","Tesla Q3 deliveries miss analyst estimates by 12%","NEGATIVE",-3.1,"Earnings/Financial"),
    ("TSLA","Elon Musk Twitter acquisition raises concerns over Tesla focus","NEGATIVE",-5.2,"Leadership Change"),
    ("TSLA","NHTSA opens investigation into Tesla autopilot following fatal crashes","STRONG_NEGATIVE",-6.1,"Regulatory/Legal"),
    ("TSLA","Tesla cuts prices globally for third time this year","NEGATIVE",-2.4,"Earnings/Financial"),
    ("TSLA","Tesla reports record Q4 deliveries of 484507 vehicles","STRONG_POSITIVE",5.8,"Earnings/Financial"),
    ("TSLA","Tesla Cybertruck launch event draws massive pre-order numbers","POSITIVE",3.2,"Product Launch"),
    ("TSLA","Tesla energy storage deployments hit record 14.7 GWh in Q3","POSITIVE",2.9,"Business Milestone"),
    ("TSLA","Tesla FSD v12 receives rave reviews from beta testers","POSITIVE",4.1,"Product Launch"),
    ("TSLA","Tesla Supercharger network opens to third-party EVs in Europe","POSITIVE",1.8,"Business Milestone"),
    ("TSLA","Tesla Berlin gigafactory ramps output to 5000 units per week","POSITIVE",2.4,"Business Milestone"),
    ("AAPL","Apple reports record Q4 revenue of $119.6B beats by $4.5B","STRONG_POSITIVE",4.8,"Earnings/Financial"),
    ("AAPL","Apple Vision Pro pre-orders sell out within hours of launch","STRONG_POSITIVE",6.2,"Product Launch"),
    ("AAPL","Apple iPhone 15 Pro demand exceeds supply as delivery times extend","POSITIVE",3.4,"Product Launch"),
    ("AAPL","Apple Services revenue hits record $22.3B in Q2 up 14% YoY","POSITIVE",2.8,"Earnings/Financial"),
    ("AAPL","Apple announces $110B share buyback programme","POSITIVE",3.9,"Earnings/Financial"),
    ("AAPL","Apple misses China revenue estimates as Huawei comeback bites","NEGATIVE",-2.6,"Earnings/Financial"),
    ("AAPL","Apple faces DOJ antitrust suit over smartphone market dominance","STRONG_NEGATIVE",-4.2,"Regulatory/Legal"),
    ("AAPL","iPhone shipments decline 10% in Q1 amid weak consumer demand","NEGATIVE",-3.1,"Earnings/Financial"),
    ("AAPL","Apple secures multi-year deal with OpenAI to power Siri AI","POSITIVE",4.2,"M&A Activity"),
    ("GOOGL","Alphabet Q3 earnings beat estimates cloud revenue up 28%","STRONG_POSITIVE",5.1,"Earnings/Financial"),
    ("GOOGL","Google launches Gemini Ultra AI model outperforms GPT-4 on benchmarks","POSITIVE",3.7,"Product Launch"),
    ("GOOGL","DOJ antitrust trial against Google reaches closing arguments","STRONG_NEGATIVE",-3.8,"Regulatory/Legal"),
    ("GOOGL","Google faces $5B fine from EU over Android antitrust breach","STRONG_NEGATIVE",-4.0,"Regulatory/Legal"),
    ("GOOGL","Waymo autonomous vehicle units surpass 1M paid trips milestone","POSITIVE",2.6,"Business Milestone"),
    ("GOOGL","Google cuts 12000 jobs as cost discipline reshapes workforce","NEGATIVE",-2.1,"Leadership Change"),
    ("MSFT","Microsoft Azure revenue grows 29% cloud dominance continues","STRONG_POSITIVE",4.4,"Earnings/Financial"),
    ("MSFT","Microsoft Copilot AI integration drives Office 365 upgrades","POSITIVE",3.2,"Product Launch"),
    ("MSFT","Microsoft completes Activision acquisition for $68.7B","POSITIVE",2.1,"M&A Activity"),
    ("MSFT","EU opens new investigation into Microsoft Teams bundling","NEGATIVE",-1.8,"Regulatory/Legal"),
    ("MSFT","Microsoft announces $10B investment in OpenAI partnership","POSITIVE",3.8,"M&A Activity"),
    ("NVDA","NVIDIA Q2 revenue blasts past estimates data center up 141%","STRONG_POSITIVE",14.2,"Earnings/Financial"),
    ("NVDA","NVIDIA H100 chip waitlist extends to 12 months on AI demand surge","STRONG_POSITIVE",8.9,"Business Milestone"),
    ("NVDA","NVIDIA announces Blackwell B200 GPU 30x faster than H100","STRONG_POSITIVE",9.3,"Product Launch"),
    ("NVDA","US restricts NVIDIA A800 chip exports to China second round","STRONG_NEGATIVE",-6.3,"Regulatory/Legal"),
    ("NVDA","NVIDIA Jensen Huang announces next-gen Rubin architecture","POSITIVE",5.1,"Product Launch"),
    ("AMZN","Amazon AWS revenue surges 17% beats estimates strong margins","STRONG_POSITIVE",4.8,"Earnings/Financial"),
    ("AMZN","Amazon acquires iRobot deal collapses under EU antitrust pressure","NEGATIVE",-2.1,"Regulatory/Legal"),
    ("AMZN","Amazon Prime membership crosses 200M global subscribers","POSITIVE",3.1,"Business Milestone"),
    ("AMZN","Amazon announces $4B investment in Anthropic AI startup","POSITIVE",2.9,"M&A Activity"),
    ("AMZN","Amazon lays off 18000 employees as cost-cutting intensifies","NEGATIVE",-3.2,"Leadership Change"),
    ("RELIANCE","Reliance Jio crosses 500M subscribers stock rallies 4%","STRONG_POSITIVE",6.2,"Business Milestone"),
    ("RELIANCE","Reliance Q3 profit beats estimates retail segment shines","POSITIVE",3.8,"Earnings/Financial"),
    ("RELIANCE","Reliance New Energy announces 100GW solar target by 2030","POSITIVE",4.1,"Product Launch"),
    ("RELIANCE","Reliance acquires majority stake in Metro Cash and Carry India","POSITIVE",2.7,"M&A Activity"),
    ("TCS","TCS Q2 revenue guidance disappoints management warns of budget freeze","NEGATIVE",-3.4,"Earnings/Financial"),
    ("TCS","TCS wins $1.5B deal with German manufacturing giant","POSITIVE",4.2,"M&A Activity"),
    ("TCS","TCS Q4 beats estimates revenue up 8.2% YoY","POSITIVE",2.9,"Earnings/Financial"),
    ("TCS","TCS announces 40000 fresher hiring plan for next fiscal year","POSITIVE",1.4,"Business Milestone"),
    ("INFY","Infosys wins $1.8B deal with European bank for core modernisation","POSITIVE",4.5,"M&A Activity"),
    ("INFY","Infosys cuts revenue guidance for second consecutive quarter","STRONG_NEGATIVE",-5.1,"Earnings/Financial"),
    ("INFY","Infosys Q3 results beat estimates margins expand on cost discipline","POSITIVE",3.3,"Earnings/Financial"),
    ("INFY","Infosys faces US visa fraud allegations whistleblower complaint","NEGATIVE",-2.9,"Regulatory/Legal"),
    ("WIPRO","Wipro acquires Capco in $1.45B consulting deal","POSITIVE",3.7,"M&A Activity"),
    ("WIPRO","Wipro misses revenue estimates for third consecutive quarter","NEGATIVE",-2.9,"Earnings/Financial"),
    ("WIPRO","Wipro announces $500M buyback amid strong free cash flow","POSITIVE",2.3,"Earnings/Financial"),
    ("WIPRO","Wipro CEO Thierry Delaporte steps down abruptly","NEGATIVE",-4.1,"Leadership Change"),
    ("HDFCBANK","HDFC Bank NIM pressure continues amid high cost of funds post-merger","NEGATIVE",-2.4,"Earnings/Financial"),
    ("HDFCBANK","HDFC Bank RBI bars new credit card issuance over IT governance failures","STRONG_NEGATIVE",-4.8,"Regulatory/Legal"),
    ("HDFCBANK","HDFC Bank Q4 profit jumps 37% merger synergies visible","STRONG_POSITIVE",5.4,"Earnings/Financial"),
    ("HDFCBANK","HDFC Bank raises $1B via AT1 bonds at competitive rates","POSITIVE",1.7,"Debt/Credit"),
]


def ensure_sample_data() -> str:
    """Return path to news.csv, generating it if it does not exist."""
    # Always ensure the hierarchy JSON exists first
    ensure_hierarchy()

    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, "data", "news.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        return path

    rng = random.Random(42)
    np.random.seed(42)
    base_date = datetime(2022, 1, 1)
    rows = []

    for i, (tkr, hl, sent, t3, evt) in enumerate(_BASE_ROWS):
        rows.append({
            "Ticker": tkr,
            "Headline": hl,
            "Sentiment": sent,
            "t3_move_pct": round(t3 + float(np.random.normal(0, 0.3)), 2),
            "EventType": evt,
            "Date": (base_date + timedelta(days=i * 7)).strftime("%Y-%m-%d"),
        })

    # Pad to 200+ rows with minor paraphrased variants (no suffix noise)
    _SYNONYMS = [
        ("reports", "announces"), ("rises", "surges"), ("falls", "drops"),
        ("beats", "exceeds"), ("misses", "disappoints"), ("wins", "secures"),
        ("cuts", "reduces"), ("launches", "unveils"), ("faces", "confronts"),
    ]
    while len(rows) < 200:
        base = rng.choice(_BASE_ROWS)
        tkr, hl, sent, t3, evt = base
        # Apply a random synonym swap to create a genuine paraphrase
        new_hl = hl
        for a, b in rng.sample(_SYNONYMS, k=min(2, len(_SYNONYMS))):
            new_hl = new_hl.replace(a, b) if rng.random() > 0.5 else new_hl.replace(b, a)
        rows.append({
            "Ticker": tkr,
            "Headline": new_hl,
            "Sentiment": sent,
            "t3_move_pct": round(t3 + float(np.random.normal(0, 1.5)), 2),
            "EventType": evt,
            "Date": (base_date + timedelta(days=len(rows) * 3)).strftime("%Y-%m-%d"),
        })

    pd.DataFrame(rows).to_csv(path, index=False)
    return path
