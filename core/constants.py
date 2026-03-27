"""
core/constants.py — Shared constants across pages and core modules.
Eliminates duplication of _TKR_NAME and _EXAMPLES across multiple files.
"""
from __future__ import annotations

TICKER_NAMES: dict[str, str] = {
    "TSLA":     "Tesla, Inc.",
    "AAPL":     "Apple Inc.",
    "GOOGL":    "Alphabet Inc.",
    "MSFT":     "Microsoft Corp.",
    "NVDA":     "NVIDIA Corp.",
    "AMZN":     "Amazon.com Inc.",
    "RELIANCE": "Reliance Industries",
    "TCS":      "Tata Consultancy Services",
    "INFY":     "Infosys Ltd.",
    "WIPRO":    "Wipro Ltd.",
    "HDFCBANK": "HDFC Bank Ltd.",
}

EXAMPLE_HEADLINES: list[tuple[str, str]] = [
    ("Tesla faces record $4.2B EU fine over autopilot safety violations",              "TSLA"),
    ("Apple reports record Q4 revenue, beats estimates by $4.5B",                     "AAPL"),
    ("Reliance Jio crosses 500M subscribers, stock rallies 4%",                       "RELIANCE"),
    ("NVIDIA CEO Jensen Huang resigns citing personal health reasons",                 "NVDA"),
    ("TCS Q2 revenue guidance disappoints, management warns of budget freeze",         "TCS"),
    ("Amazon acquires Anthropic for $15B in landmark AI deal",                        "AMZN"),
    ("Infosys wins $1.8B deal with European bank for core modernisation",             "INFY"),
    ("HDFC Bank barred from issuing new credit cards due to IT governance failures",  "HDFCBANK"),
    ("Microsoft Azure revenue grows 29% — AI workloads accelerate cloud growth",      "MSFT"),
    ("Google faces $5B EU fine over Android antitrust practices",                     "GOOGL"),
    ("WIPRO announces $500M buyback amid strong free cash flow generation",           "WIPRO"),
    ("Infosys cuts annual revenue guidance for second consecutive quarter",            "INFY"),
]
