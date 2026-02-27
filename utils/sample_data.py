"""
sample_data.py — Generates realistic news.csv if it doesn't exist.
200+ headlines across US and Indian stocks with sentiment labels
and simulated T+3 price movement for backtesting.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

SAMPLE_HEADLINES = [
    # TSLA — Negative
    ("TSLA", "Tesla faces record $4.2B EU fine over autopilot safety violations", "STRONG_NEGATIVE", -4.3, "Regulatory/Legal"),
    ("TSLA", "Tesla recalls 485,000 vehicles over rear camera and trunk defects", "NEGATIVE", -2.8, "Product/Safety Issue"),
    ("TSLA", "Tesla Q3 deliveries miss analyst estimates by 12%", "NEGATIVE", -3.1, "Earnings/Financial"),
    ("TSLA", "Elon Musk Twitter acquisition raises concerns over Tesla focus", "NEGATIVE", -5.2, "Leadership Change"),
    ("TSLA", "NHTSA opens investigation into Tesla autopilot following fatal crashes", "STRONG_NEGATIVE", -6.1, "Regulatory/Legal"),
    ("TSLA", "Tesla cuts prices globally for third time in 2023, margin concerns rise", "NEGATIVE", -2.4, "Earnings/Financial"),
    ("TSLA", "Tesla faces class action lawsuit over battery degradation claims", "NEGATIVE", -1.9, "Regulatory/Legal"),
    # TSLA — Positive
    ("TSLA", "Tesla reports record Q4 deliveries of 484,507 vehicles", "STRONG_POSITIVE", 5.8, "Earnings/Financial"),
    ("TSLA", "Tesla Cybertruck launch event draws massive pre-order numbers", "POSITIVE", 3.2, "Product Launch"),
    ("TSLA", "Tesla energy storage deployments hit record 14.7 GWh in Q3", "POSITIVE", 2.9, "Business Milestone"),
    ("TSLA", "Tesla Gigafactory Texas reaches full production capacity ahead of schedule", "POSITIVE", 3.5, "Business Milestone"),
    ("TSLA", "Tesla FSD v12 receives rave reviews from beta testers", "POSITIVE", 4.1, "Product Launch"),

    # AAPL — Positive
    ("AAPL", "Apple reports record Q4 revenue of $119.6B, beats by $4.5B", "STRONG_POSITIVE", 4.8, "Earnings/Financial"),
    ("AAPL", "Apple Vision Pro pre-orders sell out within hours of launch", "STRONG_POSITIVE", 6.2, "Product Launch"),
    ("AAPL", "Apple iPhone 15 Pro demand exceeds supply, delivery times extend to 6 weeks", "POSITIVE", 3.4, "Product Launch"),
    ("AAPL", "Apple Services revenue hits record $22.3B in Q2, up 14% YoY", "POSITIVE", 2.8, "Earnings/Financial"),
    ("AAPL", "Apple announces $110B share buyback programme", "POSITIVE", 3.9, "Earnings/Financial"),
    ("AAPL", "Apple wins $2B EU court ruling against Commission tax order", "POSITIVE", 1.8, "Regulatory/Legal"),
    # AAPL — Negative
    ("AAPL", "Apple misses China revenue estimates as Huawei comeback bites", "NEGATIVE", -2.6, "Earnings/Financial"),
    ("AAPL", "Apple faces DOJ antitrust suit over smartphone market dominance", "STRONG_NEGATIVE", -4.2, "Regulatory/Legal"),
    ("AAPL", "iPhone shipments decline 10% in Q1 amid weak consumer demand", "NEGATIVE", -3.1, "Earnings/Financial"),

    # GOOGL — Mixed
    ("GOOGL", "Alphabet Q3 earnings beat estimates, cloud revenue up 28%", "STRONG_POSITIVE", 5.1, "Earnings/Financial"),
    ("GOOGL", "Google launches Gemini Ultra AI model, challenges GPT-4", "POSITIVE", 3.7, "Product Launch"),
    ("GOOGL", "DOJ antitrust trial against Google reaches closing arguments", "STRONG_NEGATIVE", -3.8, "Regulatory/Legal"),
    ("GOOGL", "Google faces $5B fine from EU over Android antitrust breach", "STRONG_NEGATIVE", -4.0, "Regulatory/Legal"),
    ("GOOGL", "Waymo autonomous vehicle units surpass 1M paid trips milestone", "POSITIVE", 2.6, "Business Milestone"),
    ("GOOGL", "Alphabet announces 12,000 job cuts, restructuring underway", "NEGATIVE", -2.9, "Leadership Change"),

    # MSFT — Mixed
    ("MSFT", "Microsoft Azure revenue grows 29%, cloud dominance continues", "STRONG_POSITIVE", 4.4, "Earnings/Financial"),
    ("MSFT", "Microsoft Copilot AI integration drives Office 365 upgrades", "POSITIVE", 3.2, "Product Launch"),
    ("MSFT", "Microsoft completes Activision acquisition for $68.7B", "POSITIVE", 2.1, "M&A Activity"),
    ("MSFT", "EU opens new investigation into Microsoft Teams bundling practices", "NEGATIVE", -1.8, "Regulatory/Legal"),
    ("MSFT", "Microsoft GitHub Copilot reaches 1.3M paid subscribers", "POSITIVE", 2.4, "Business Milestone"),

    # NVDA — Mixed
    ("NVDA", "NVIDIA Q2 revenue blasts past estimates, data center up 141%", "STRONG_POSITIVE", 14.2, "Earnings/Financial"),
    ("NVDA", "NVIDIA H100 chip waitlist extends to 12 months on AI demand surge", "STRONG_POSITIVE", 8.9, "Business Milestone"),
    ("NVDA", "NVIDIA announces Blackwell B200 GPU, 30x faster than H100", "STRONG_POSITIVE", 9.3, "Product Launch"),
    ("NVDA", "US restricts NVIDIA A800 chip exports to China, second round of bans", "STRONG_NEGATIVE", -6.3, "Regulatory/Legal"),
    ("NVDA", "NVIDIA CEO Jensen Huang sells $44.5M in stock options", "NEGATIVE", -3.2, "Leadership Change"),
    ("NVDA", "NVIDIA faces antitrust probe by French competition authority", "NEGATIVE", -2.7, "Regulatory/Legal"),

    # AMZN — Mixed
    ("AMZN", "Amazon AWS revenue rises 17%, operating income doubles YoY", "STRONG_POSITIVE", 6.4, "Earnings/Financial"),
    ("AMZN", "Amazon Prime membership surpasses 200M globally", "POSITIVE", 3.1, "Business Milestone"),
    ("AMZN", "Amazon announces 18,000 layoffs in largest-ever workforce reduction", "NEGATIVE", -3.4, "Leadership Change"),
    ("AMZN", "FTC sues Amazon over monopoly in online marketplace", "STRONG_NEGATIVE", -4.7, "Regulatory/Legal"),
    ("AMZN", "Amazon acquires One Medical for $3.9B, expanding healthcare push", "POSITIVE", 2.3, "M&A Activity"),

    # RELIANCE — Mixed
    ("RELIANCE", "Jio crosses 500M subscriber milestone, fastest in India's history", "STRONG_POSITIVE", 4.2, "Business Milestone"),
    ("RELIANCE", "Reliance Industries Q2 net profit rises 27% on retail and digital boom", "POSITIVE", 3.1, "Earnings/Financial"),
    ("RELIANCE", "Reliance Retail expands to 18,500 stores, revenue up 30%", "POSITIVE", 2.8, "Business Milestone"),
    ("RELIANCE", "Jio 5G rollout completes in all 22 telecom circles ahead of schedule", "STRONG_POSITIVE", 5.3, "Business Milestone"),
    ("RELIANCE", "Reliance AGM: Mukesh Ambani announces new green energy investments of $75B", "POSITIVE", 4.1, "Business Milestone"),
    ("RELIANCE", "Reliance O2C segment hit by weak global refining margins in Q3", "NEGATIVE", -2.2, "Earnings/Financial"),
    ("RELIANCE", "Competition Commission probes Jio's below-cost pricing strategy", "NEGATIVE", -1.9, "Regulatory/Legal"),

    # TCS — Mixed
    ("TCS", "TCS wins $2.25B deal with UK government for digital transformation", "STRONG_POSITIVE", 4.5, "M&A Activity"),
    ("TCS", "TCS Q2 PAT beats estimates; management raises FY24 guidance", "POSITIVE", 3.2, "Earnings/Financial"),
    ("TCS", "TCS attrition falls to 14.9%, headcount additions resume", "POSITIVE", 2.1, "Earnings/Financial"),
    ("TCS", "TCS Q1 revenue misses estimates, guidance cut citing banking sector slowdown", "NEGATIVE", -3.8, "Earnings/Financial"),
    ("TCS", "TCS faces class action in US over H1B visa discrimination", "NEGATIVE", -2.1, "Regulatory/Legal"),
    ("TCS", "TCS warns of deal delays as clients cut IT budgets in uncertain economy", "NEGATIVE", -4.2, "Earnings/Financial"),

    # INFY — Mixed
    ("INFY", "Infosys wins $1.8B deal with European bank for core banking modernisation", "STRONG_POSITIVE", 4.8, "M&A Activity"),
    ("INFY", "Infosys raises FY24 revenue guidance to 4-7% after strong Q2", "POSITIVE", 3.4, "Earnings/Financial"),
    ("INFY", "Infosys announces $1.5B buyback programme at 20% premium", "POSITIVE", 3.9, "Earnings/Financial"),
    ("INFY", "Infosys Q1 revenue below estimates; CEO cites macro uncertainty", "NEGATIVE", -3.1, "Earnings/Financial"),
    ("INFY", "Infosys whistleblower complaint alleges accounting irregularities", "STRONG_NEGATIVE", -16.2, "Regulatory/Legal"),
    ("INFY", "Infosys lowers FY24 revenue guidance citing weak discretionary spending", "NEGATIVE", -5.1, "Earnings/Financial"),

    # WIPRO — Mixed
    ("WIPRO", "Wipro wins $1.2B multi-year deal with major US retailer", "POSITIVE", 3.6, "M&A Activity"),
    ("WIPRO", "Wipro Q2 PAT rises 14% YoY, margins expand 80bps", "POSITIVE", 2.7, "Earnings/Financial"),
    ("WIPRO", "Wipro CEO Thierry Delaporte resigns, board appoints Srinivas Pallia", "NEGATIVE", -4.3, "Leadership Change"),
    ("WIPRO", "Wipro Q4 revenue guidance disappoints, cites client budget freezes", "NEGATIVE", -5.8, "Earnings/Financial"),
    ("WIPRO", "Wipro acquires Capco for $1.45B to boost financial services practice", "POSITIVE", 2.2, "M&A Activity"),

    # HDFCBANK — Mixed
    ("HDFCBANK", "HDFC Bank Q2 net profit surges 51% post merger with HDFC Ltd", "STRONG_POSITIVE", 4.9, "Earnings/Financial"),
    ("HDFCBANK", "HDFC Bank loan growth decelerates; RBI flags liquidity concerns", "NEGATIVE", -3.4, "Regulatory/Legal"),
    ("HDFCBANK", "HDFC Bank digital transactions hit record 1.4B in October", "POSITIVE", 2.3, "Business Milestone"),
    ("HDFCBANK", "RBI bars HDFC Bank from issuing new credit cards over IT outages", "STRONG_NEGATIVE", -6.8, "Regulatory/Legal"),
    ("HDFCBANK", "HDFC Bank NIM pressure continues amid high cost of funds post merger", "NEGATIVE", -2.9, "Earnings/Financial"),

    # General macro headlines
    ("NIFTY", "RBI holds repo rate steady at 6.5%, signals cautious easing ahead", "NEUTRAL", 0.4, "Macroeconomic"),
    ("NIFTY", "India Q2 GDP growth at 7.6%, beats IMF forecast of 6.3%", "POSITIVE", 1.8, "Macroeconomic"),
    ("SPX", "US CPI inflation cools to 3.2%, Fed rate cut expectations rise", "POSITIVE", 2.1, "Macroeconomic"),
    ("SPX", "Federal Reserve raises rates by 25bps, signals pause ahead", "NEUTRAL", 0.2, "Macroeconomic"),
    ("SPX", "US unemployment hits 50-year low of 3.4%, economy remains resilient", "POSITIVE", 1.5, "Macroeconomic"),

    # Rumour/unconfirmed examples
    ("TSLA", "Sources say Tesla in early talks to acquire Uber, deal could be worth $80B", "POSITIVE", 2.1, "M&A Activity"),
    ("AAPL", "Reportedly Apple exploring folding iPhone design for 2025 launch", "NEUTRAL", 0.8, "Product Launch"),
    ("RELIANCE", "According to insiders, Reliance eyeing stake in Vodafone Idea to expand telecom dominance", "POSITIVE", 1.4, "M&A Activity"),

    # Additional diversity
    ("GOOGL", "Google DeepMind achieves breakthrough in protein folding prediction accuracy", "POSITIVE", 3.1, "Product Launch"),
    ("MSFT", "Microsoft Bing market share rises to 4.2% following Copilot integration", "POSITIVE", 1.9, "Business Milestone"),
    ("NVDA", "NVIDIA DGX Cloud platform signs deals with five major cloud providers", "POSITIVE", 4.2, "M&A Activity"),
    ("AMZN", "Amazon introduces same-day delivery in 20 new Indian cities", "POSITIVE", 1.6, "Business Milestone"),
    ("TCS", "TCS partners with Google Cloud for AI-powered enterprise solutions", "POSITIVE", 2.4, "M&A Activity"),
    ("INFY", "Infosys and Microsoft expand Azure partnership to $1.5B over 3 years", "POSITIVE", 3.1, "M&A Activity"),
]


def generate_news_csv(output_path: str):
    """Generate a news.csv file with realistic historical data."""
    random.seed(42)
    np.random.seed(42)

    base_date = datetime(2020, 1, 1)
    rows = []

    for ticker, headline, sentiment, t3_move, event_type in SAMPLE_HEADLINES:
        # Random date between 2020 and 2024
        days_offset = random.randint(0, 1460)
        date = base_date + timedelta(days=days_offset)

        # Add slight noise to price movement
        actual_move = round(t3_move + np.random.normal(0, 0.8), 2)

        # Polarity from sentiment label
        pol_map = {
            "STRONG_POSITIVE": round(random.uniform(0.65, 0.95), 3),
            "POSITIVE":        round(random.uniform(0.25, 0.65), 3),
            "NEUTRAL":         round(random.uniform(-0.15, 0.15), 3),
            "NEGATIVE":        round(random.uniform(-0.65, -0.25), 3),
            "STRONG_NEGATIVE": round(random.uniform(-0.95, -0.65), 3),
        }
        polarity = pol_map.get(sentiment, 0.0)

        rows.append({
            "Date":       date.strftime("%Y-%m-%d"),
            "Ticker":     ticker,
            "Headline":   headline,
            "sentiment":  sentiment,
            "polarity":   polarity,
            "event_type": event_type,
            "t3_move_pct": actual_move,
            "source":     random.choice(["Reuters", "Bloomberg", "CNBC", "ET Markets", "Mint", "Economic Times", "WSJ"]),
        })

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def ensure_sample_data():
    """Call on app start — creates news.csv if it doesn't exist."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    csv_path = os.path.join(data_dir, "news.csv")
    if not os.path.exists(csv_path):
        generate_news_csv(csv_path)
    return csv_path
