"""
core/seeder.py — Generates data/news.csv with 200+ historical headlines.
No Streamlit imports.
"""
from __future__ import annotations
import os, random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

_BASE_ROWS = [
    # (Ticker, Headline, Sentiment, T+3_move, EventType)
    ("TSLA","Tesla faces record $4.2B EU fine over autopilot safety violations","STRONG_NEGATIVE",-4.3,"Regulatory/Legal"),
    ("TSLA","Tesla recalls 485000 vehicles over rear camera defects","NEGATIVE",-2.8,"Regulatory/Legal"),
    ("TSLA","Tesla Q3 deliveries miss analyst estimates by 12%","NEGATIVE",-3.1,"Earnings/Financial"),
    ("TSLA","Elon Musk Twitter acquisition raises concerns over Tesla focus","NEGATIVE",-5.2,"Leadership Change"),
    ("TSLA","NHTSA opens investigation into Tesla autopilot following fatal crashes","STRONG_NEGATIVE",-6.1,"Regulatory/Legal"),
    ("TSLA","Tesla cuts prices globally for third time in 2024","NEGATIVE",-2.4,"Earnings/Financial"),
    ("TSLA","Tesla reports record Q4 deliveries of 484507 vehicles","STRONG_POSITIVE",5.8,"Earnings/Financial"),
    ("TSLA","Tesla Cybertruck launch event draws massive pre-order numbers","POSITIVE",3.2,"Product Launch"),
    ("TSLA","Tesla energy storage deployments hit record 14.7 GWh in Q3","POSITIVE",2.9,"Business Milestone"),
    ("TSLA","Tesla FSD v12 receives rave reviews from beta testers","POSITIVE",4.1,"Product Launch"),
    ("AAPL","Apple reports record Q4 revenue of $119.6B beats by $4.5B","STRONG_POSITIVE",4.8,"Earnings/Financial"),
    ("AAPL","Apple Vision Pro pre-orders sell out within hours of launch","STRONG_POSITIVE",6.2,"Product Launch"),
    ("AAPL","Apple iPhone 15 Pro demand exceeds supply delivery times extend","POSITIVE",3.4,"Product Launch"),
    ("AAPL","Apple Services revenue hits record $22.3B in Q2 up 14% YoY","POSITIVE",2.8,"Earnings/Financial"),
    ("AAPL","Apple announces $110B share buyback programme","POSITIVE",3.9,"Earnings/Financial"),
    ("AAPL","Apple misses China revenue estimates as Huawei comeback bites","NEGATIVE",-2.6,"Earnings/Financial"),
    ("AAPL","Apple faces DOJ antitrust suit over smartphone market dominance","STRONG_NEGATIVE",-4.2,"Regulatory/Legal"),
    ("AAPL","iPhone shipments decline 10% in Q1 amid weak consumer demand","NEGATIVE",-3.1,"Earnings/Financial"),
    ("GOOGL","Alphabet Q3 earnings beat estimates cloud revenue up 28%","STRONG_POSITIVE",5.1,"Earnings/Financial"),
    ("GOOGL","Google launches Gemini Ultra AI model challenges GPT-4","POSITIVE",3.7,"Product Launch"),
    ("GOOGL","DOJ antitrust trial against Google reaches closing arguments","STRONG_NEGATIVE",-3.8,"Regulatory/Legal"),
    ("GOOGL","Google faces $5B fine from EU over Android antitrust breach","STRONG_NEGATIVE",-4.0,"Regulatory/Legal"),
    ("GOOGL","Waymo autonomous vehicle units surpass 1M paid trips","POSITIVE",2.6,"Business Milestone"),
    ("MSFT","Microsoft Azure revenue grows 29% cloud dominance continues","STRONG_POSITIVE",4.4,"Earnings/Financial"),
    ("MSFT","Microsoft Copilot AI integration drives Office 365 upgrades","POSITIVE",3.2,"Product Launch"),
    ("MSFT","Microsoft completes Activision acquisition for $68.7B","POSITIVE",2.1,"M&A Activity"),
    ("MSFT","EU opens new investigation into Microsoft Teams bundling","NEGATIVE",-1.8,"Regulatory/Legal"),
    ("NVDA","NVIDIA Q2 revenue blasts past estimates data center up 141%","STRONG_POSITIVE",14.2,"Earnings/Financial"),
    ("NVDA","NVIDIA H100 chip waitlist extends to 12 months on AI demand","STRONG_POSITIVE",8.9,"Business Milestone"),
    ("NVDA","NVIDIA announces Blackwell B200 GPU 30x faster than H100","STRONG_POSITIVE",9.3,"Product Launch"),
    ("NVDA","US restricts NVIDIA A800 chip exports to China second round","STRONG_NEGATIVE",-6.3,"Regulatory/Legal"),
    ("AMZN","Amazon AWS revenue surges 17% beats estimates","STRONG_POSITIVE",4.8,"Earnings/Financial"),
    ("AMZN","Amazon acquires iRobot deal collapses under EU pressure","NEGATIVE",-2.1,"Regulatory/Legal"),
    ("AMZN","Amazon Prime membership crosses 200M global subscribers","POSITIVE",3.1,"Business Milestone"),
    ("RELIANCE","Reliance Jio crosses 500M subscribers stock rallies","STRONG_POSITIVE",6.2,"Business Milestone"),
    ("RELIANCE","Reliance Q3 profit beats estimates retail segment shines","POSITIVE",3.8,"Earnings/Financial"),
    ("RELIANCE","Reliance New Energy announces 100GW solar target by 2030","POSITIVE",4.1,"Product Launch"),
    ("TCS","TCS Q2 revenue guidance disappoints management warns of budget freeze","NEGATIVE",-3.4,"Earnings/Financial"),
    ("TCS","TCS wins $1.5B deal with German manufacturing giant","POSITIVE",4.2,"M&A Activity"),
    ("TCS","TCS Q4 beats estimates revenue up 8.2% YoY","POSITIVE",2.9,"Earnings/Financial"),
    ("INFY","Infosys wins $1.8B deal with European bank","POSITIVE",4.5,"M&A Activity"),
    ("INFY","Infosys cuts revenue guidance second time this year","STRONG_NEGATIVE",-5.1,"Earnings/Financial"),
    ("INFY","Infosys Q3 results beat estimates margins expand","POSITIVE",3.3,"Earnings/Financial"),
    ("WIPRO","Wipro acquires Capco in $1.45B consulting deal","POSITIVE",3.7,"M&A Activity"),
    ("WIPRO","Wipro misses revenue estimates for third consecutive quarter","NEGATIVE",-2.9,"Earnings/Financial"),
    ("HDFCBANK","HDFC Bank NIM pressure continues amid high cost of funds","NEGATIVE",-2.4,"Earnings/Financial"),
    ("HDFCBANK","HDFC Bank RBI bars new credit card issuance over IT outages","STRONG_NEGATIVE",-4.8,"Regulatory/Legal"),
    ("HDFCBANK","HDFC Bank Q4 profit jumps 37% merger benefits visible","STRONG_POSITIVE",5.4,"Earnings/Financial"),
]


def ensure_sample_data() -> str:
    """Return path to news.csv, generating it if it doesn't exist."""
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, "data", "news.csv")
    if os.path.exists(path):
        return path

    rng = random.Random(42)
    np.random.seed(42)
    base_date = datetime(2022, 1, 1)
    rows = []
    for i, (tkr, hl, sent, t3, evt) in enumerate(_BASE_ROWS):
        rows.append({
            "Ticker":      tkr,
            "Headline":    hl,
            "Sentiment":   sent,
            "t3_move_pct": round(t3 + float(np.random.normal(0, 0.3)), 2),
            "EventType":   evt,
            "Date":        (base_date + timedelta(days=i * 7)).strftime("%Y-%m-%d"),
        })
    while len(rows) < 200:
        base = rng.choice(_BASE_ROWS)
        tkr, hl, sent, t3, evt = base
        rows.append({
            "Ticker":      tkr,
            "Headline":    hl + f" (var {len(rows)})",
            "Sentiment":   sent,
            "t3_move_pct": round(t3 + float(np.random.normal(0, 1.5)), 2),
            "EventType":   evt,
            "Date":        (base_date + timedelta(days=len(rows) * 3)).strftime("%Y-%m-%d"),
        })
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path
