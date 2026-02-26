"""
stock_data.py — yFinance wrapper with caching.
Handles US (TSLA) and Indian (.NS suffix) stocks cleanly.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta


# ── TICKER NORMALISATION ──────────────────────────────────────────────────────
INDIAN_TICKERS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "WIPRO":    "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK":"ICICIBANK.NS",
    "SBIN":     "SBIN.NS",
    "BHARTIARTL":"BHARTIARTL.NS",
    "NIFTY":    "^NSEI",
    "SENSEX":   "^BSESN",
}

def normalise_ticker(ticker: str) -> str:
    """Convert friendly ticker to yFinance format."""
    t = ticker.upper().strip()
    return INDIAN_TICKERS.get(t, t)


# ── CACHED PRICE FETCH ────────────────────────────────────────────────────────
@st.cache_data(ttl=300)   # 5-minute cache
def get_current_price(ticker: str) -> dict:
    """
    Returns dict with price, change, change_pct, company_name.
    Returns safe defaults on failure.
    """
    yt = normalise_ticker(ticker)
    try:
        info = yf.Ticker(yt).fast_info
        price     = round(float(info.last_price), 2)
        prev      = round(float(info.previous_close), 2)
        change    = round(price - prev, 2)
        chg_pct   = round((change / prev) * 100, 2) if prev else 0.0
        return {
            "ticker":   ticker,
            "price":    price,
            "change":   change,
            "chg_pct":  chg_pct,
            "currency": "₹" if yt.endswith(".NS") else "$",
            "error":    False,
        }
    except Exception as e:
        return {
            "ticker":  ticker,
            "price":   0.0,
            "change":  0.0,
            "chg_pct": 0.0,
            "currency": "$",
            "error":   True,
            "msg":     str(e),
        }


@st.cache_data(ttl=900)   # 15-minute cache
def get_price_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """
    Returns OHLCV DataFrame for the last N days.
    """
    yt = normalise_ticker(ticker)
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        df    = yf.download(yt, start=start.strftime("%Y-%m-%d"),
                            end=end.strftime("%Y-%m-%d"), progress=False)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900)
def get_t3_actual_move(ticker: str, event_date: str) -> float | None:
    """
    Given an event date (YYYY-MM-DD), return the actual T+3 % price change.
    Used in historical backtesting view.
    """
    yt = normalise_ticker(ticker)
    try:
        start = datetime.strptime(event_date, "%Y-%m-%d")
        end   = start + timedelta(days=10)   # fetch a bit more for safety
        df    = yf.download(yt, start=start.strftime("%Y-%m-%d"),
                            end=end.strftime("%Y-%m-%d"), progress=False)
        if df.empty or len(df) < 2:
            return None
        p0 = float(df["Close"].iloc[0])
        # T+3 or last available
        idx = min(3, len(df) - 1)
        p3  = float(df["Close"].iloc[idx])
        return round(((p3 - p0) / p0) * 100, 2)
    except Exception:
        return None


@st.cache_data(ttl=900)
def get_bulk_prices(tickers: list[str]) -> dict:
    """Fetch current prices for a list of tickers efficiently."""
    return {t: get_current_price(t) for t in tickers}


def format_price(data: dict) -> str:
    """Format price for display: ₹2,847.50 or $218.40"""
    if data.get("error"):
        return "N/A"
    cur = data.get("currency", "$")
    p   = data.get("price", 0)
    return f"{cur}{p:,.2f}"


def format_change(data: dict) -> str:
    """Format change: +2.14% or -3.21%"""
    if data.get("error"):
        return "N/A"
    pct = data.get("chg_pct", 0)
    return f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"


def change_color(data: dict) -> str:
    """Return CSS color string for price change."""
    if data.get("error"):
        return "#7A92A8"
    return "#00E8A0" if data.get("chg_pct", 0) >= 0 else "#FF3D60"


# ── WATCHLIST BULK ────────────────────────────────────────────────────────────
DEFAULT_WATCHLIST_TICKERS = [
    "TSLA", "AAPL", "NVDA", "MSFT", "GOOGL",
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO",
]
