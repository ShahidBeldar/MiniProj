"""
core/stocks.py — yFinance price wrapper. No Streamlit imports.
Cached at the Streamlit layer via @st.cache_data in callers.
"""
from __future__ import annotations
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# NSE ticker mapping for Indian stocks
_INDIAN: dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "WIPRO":    "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK":"ICICIBANK.NS",
    "BAJFINANCE":"BAJFINANCE.NS",
}


def _yt(ticker: str) -> str:
    return _INDIAN.get(ticker.upper(), ticker.upper())


def get_price(ticker: str) -> dict:
    """Return price dict: {ticker, price, change, chg_pct, currency, error}."""
    try:
        info = yf.Ticker(_yt(ticker)).fast_info
        p    = round(float(info.last_price), 2)
        prev = round(float(info.previous_close), 2)
        chg  = round(p - prev, 2)
        chgp = round((chg / prev) * 100, 2) if prev else 0.0
        return {
            "ticker":   ticker,
            "price":    p,
            "change":   chg,
            "chg_pct":  chgp,
            "currency": "₹" if ticker in _INDIAN else "$",
            "error":    False,
        }
    except Exception as e:
        return {
            "ticker":   ticker,
            "price":    0.0,
            "change":   0.0,
            "chg_pct":  0.0,
            "currency": "$",
            "error":    True,
            "msg":      str(e),
        }


def get_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """Return OHLCV DataFrame for the last `days` calendar days."""
    try:
        end   = datetime.today()
        start = end - timedelta(days=days)
        df = yf.download(
            _yt(ticker),
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
        df.index = pd.to_datetime(df.index)
        # Flatten multi-level columns that yf sometimes returns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def fmt_price(d: dict) -> str:
    if d.get("error"):
        return "N/A"
    return f"{d.get('currency','$')}{d.get('price',0):,.2f}"


def fmt_change(d: dict) -> str:
    if d.get("error"):
        return "N/A"
    p = d.get("chg_pct", 0)
    return f"+{p:.2f}%" if p >= 0 else f"{p:.2f}%"


def chg_color(d: dict) -> str:
    if d.get("error"):
        return "#7A92A8"
    return "#00E8A0" if d.get("chg_pct", 0) >= 0 else "#FF3D60"
