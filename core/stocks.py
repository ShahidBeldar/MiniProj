"""
core/stocks.py — yFinance wrapper with full OHLCV, technical indicators,
multi-ticker comparison, intraday support, and global market index data.
Pure Python — no Streamlit imports. Callers wrap with @st.cache_data.
"""
from __future__ import annotations
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── TICKER MAPPINGS ───────────────────────────────────────────────────────────
_INDIAN: dict[str, str] = {
    "RELIANCE":  "RELIANCE.NS",
    "TCS":       "TCS.NS",
    "INFY":      "INFY.NS",
    "WIPRO":     "WIPRO.NS",
    "HDFCBANK":  "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "BAJFINANCE":"BAJFINANCE.NS",
}

# Major global indices exposed in Market page
MARKET_INDICES: dict[str, str] = {
    "S&P 500":    "^GSPC",
    "NASDAQ":     "^IXIC",
    "DOW JONES":  "^DJI",
    "VIX":        "^VIX",
    "NIFTY 50":   "^NSEI",
    "SENSEX":     "^BSESN",
    "FTSE 100":   "^FTSE",
    "NIKKEI 225": "^N225",
    "HANG SENG":  "^HSI",
    "DAX":        "^GDAXI",
}

# Period → (yf period string, interval) — used in Market page dropdowns
PERIOD_OPTIONS: dict[str, tuple[str, str]] = {
    "1 Day":    ("1d",  "5m"),
    "5 Days":   ("5d",  "15m"),
    "1 Month":  ("1mo", "1d"),
    "3 Months": ("3mo", "1d"),
    "6 Months": ("6mo", "1d"),
    "1 Year":   ("1y",  "1wk"),
    "2 Years":  ("2y",  "1wk"),
    "5 Years":  ("5y",  "1mo"),
}

ALL_TICKERS = list(_INDIAN.keys()) + [
    "TSLA", "AAPL", "GOOGL", "MSFT", "NVDA", "AMZN"
]


def _yt(ticker: str) -> str:
    """Map display ticker → yfinance symbol."""
    return _INDIAN.get(ticker.upper(), ticker.upper())


# ── PRICE ────────────────────────────────────────────────────────────────────

def get_price(ticker: str) -> dict:
    """Live price dict: {ticker, price, change, chg_pct, currency, error}."""
    try:
        info = yf.Ticker(_yt(ticker)).fast_info
        p    = round(float(info.last_price),      2)
        prev = round(float(info.previous_close),  2)
        chg  = round(p - prev, 2)
        chgp = round((chg / prev) * 100, 2) if prev else 0.0
        return {"ticker": ticker, "price": p, "change": chg, "chg_pct": chgp,
                "currency": "₹" if ticker in _INDIAN else "$", "error": False}
    except Exception as e:
        return {"ticker": ticker, "price": 0.0, "change": 0.0, "chg_pct": 0.0,
                "currency": "$", "error": True, "msg": str(e)}


def get_index_prices() -> dict[str, dict]:
    """Fetch live price for all MARKET_INDICES. Returns {name: price_dict}."""
    out: dict[str, dict] = {}
    for name, sym in MARKET_INDICES.items():
        try:
            info = yf.Ticker(sym).fast_info
            p    = round(float(info.last_price),     2)
            prev = round(float(info.previous_close), 2)
            chg  = round(p - prev, 2)
            chgp = round((chg / prev) * 100, 2) if prev else 0.0
            out[name] = {"symbol": sym, "price": p, "change": chg,
                         "chg_pct": chgp, "error": False}
        except Exception as e:
            out[name] = {"symbol": sym, "price": 0.0, "change": 0.0,
                         "chg_pct": 0.0, "error": True, "msg": str(e)}
    return out


# ── OHLCV ────────────────────────────────────────────────────────────────────

def get_ohlcv(ticker: str, period_label: str = "3 Months") -> pd.DataFrame:
    """
    Fetch OHLCV for the given period_label key from PERIOD_OPTIONS.
    Returns clean DataFrame with columns: Open, High, Low, Close, Volume.
    """
    period, interval = PERIOD_OPTIONS.get(period_label, ("3mo", "1d"))
    try:
        df = yf.download(
            _yt(ticker), period=period, interval=interval,
            progress=False, auto_adjust=True,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [str(c[0]) for c in df.columns]
        # Normalise column names
        rename: dict[str, str] = {}
        for c in df.columns:
            cl = str(c).lower()
            if cl == "open":    rename[c] = "Open"
            elif cl == "high":  rename[c] = "High"
            elif cl == "low":   rename[c] = "Low"
            elif cl == "close": rename[c] = "Close"
            elif "vol" in cl:   rename[c] = "Volume"
        df = df.rename(columns=rename)
        keep = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
        return df[keep].dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()


def get_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """Backwards-compat shim — maps days → period_label → get_ohlcv."""
    label = (
        "1 Day"    if days <=  1 else
        "5 Days"   if days <=  5 else
        "1 Month"  if days <= 31 else
        "3 Months" if days <= 92 else
        "6 Months" if days <= 183 else
        "1 Year"
    )
    return get_ohlcv(ticker, label)


# ── TECHNICAL INDICATORS ─────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach technical indicators to an OHLCV DataFrame (in-place copy).
    Adds: MA20, MA50, MA200, EMA12, EMA26, MACD, MACD_Signal, MACD_Hist,
          BB_Upper, BB_Mid, BB_Lower, RSI, ATR, VWAP.
    Requires at least a 'Close' column; uses High/Low/Volume when present.
    """
    if df.empty or "Close" not in df.columns:
        return df
    df = df.copy()

    c = df["Close"]
    h = df["High"]   if "High"   in df.columns else c
    l = df["Low"]    if "Low"    in df.columns else c
    v = df["Volume"] if "Volume" in df.columns else pd.Series(0, index=df.index)

    # Simple moving averages
    df["MA20"]  = c.rolling(20,  min_periods=1).mean().round(4)
    df["MA50"]  = c.rolling(50,  min_periods=1).mean().round(4)
    df["MA200"] = c.rolling(200, min_periods=1).mean().round(4)

    # EMA & MACD
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["EMA12"]       = ema12.round(4)
    df["EMA26"]       = ema26.round(4)
    df["MACD"]        = (ema12 - ema26).round(4)
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean().round(4)
    df["MACD_Hist"]   = (df["MACD"] - df["MACD_Signal"]).round(4)

    # Bollinger Bands (20-period, 2σ)
    std20          = c.rolling(20, min_periods=1).std()
    df["BB_Mid"]   = df["MA20"]
    df["BB_Upper"] = (df["MA20"] + 2 * std20).round(4)
    df["BB_Lower"] = (df["MA20"] - 2 * std20).round(4)

    # RSI (14)
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss  = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = (100 - 100 / (1 + rs)).round(2)

    # ATR (14)
    tr  = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14, min_periods=1).mean().round(4)

    # VWAP (cumulative approximation)
    typical   = (h + l + c) / 3
    cum_tp_v  = (typical * v).cumsum()
    cum_v     = v.cumsum().replace(0, np.nan)
    df["VWAP"] = (cum_tp_v / cum_v).round(4)

    return df


def get_ohlcv_with_indicators(ticker: str, period_label: str = "3 Months") -> pd.DataFrame:
    """Convenience: fetch OHLCV then attach all indicators."""
    df = get_ohlcv(ticker, period_label)
    return add_indicators(df) if not df.empty else df


def get_multi_ticker(
    tickers: list[str], period_label: str = "3 Months"
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV+indicators for several tickers. Returns {ticker: df}."""
    return {t: get_ohlcv_with_indicators(t, period_label) for t in tickers}


# ── COMPANY INFO ──────────────────────────────────────────────────────────────

def get_ticker_info(ticker: str) -> dict:
    """Return company metadata dict from yfinance .info."""
    try:
        info = yf.Ticker(_yt(ticker)).info or {}
        mc   = info.get("marketCap") or 0
        mc_s = (f"${mc/1e12:.2f}T" if mc >= 1e12 else
                f"${mc/1e9:.2f}B"  if mc >= 1e9  else
                f"${mc/1e6:.2f}M"  if mc >= 1e6  else "N/A")
        return {
            "name":         info.get("longName") or info.get("shortName") or ticker,
            "sector":       info.get("sector",   "N/A"),
            "industry":     info.get("industry", "N/A"),
            "market_cap":   mc_s,
            "pe_ratio":     round(float(info.get("trailingPE")  or 0), 2),
            "eps":          round(float(info.get("trailingEps") or 0), 2),
            "week52_high":  round(float(info.get("fiftyTwoWeekHigh") or 0), 2),
            "week52_low":   round(float(info.get("fiftyTwoWeekLow")  or 0), 2),
            "avg_volume":   info.get("averageVolume") or 0,
            "beta":         round(float(info.get("beta")         or 0), 2),
            "dividend_yield": round(float(info.get("dividendYield") or 0) * 100, 2),
            "description":  (info.get("longBusinessSummary") or "")[:400],
            "error": False,
        }
    except Exception as e:
        return {"name": ticker, "error": True, "msg": str(e)}


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────

def fmt_price(d: dict) -> str:
    if d.get("error"): return "N/A"
    return f"{d.get('currency','$')}{d.get('price',0):,.2f}"


def fmt_change(d: dict) -> str:
    if d.get("error"): return "N/A"
    p = d.get("chg_pct", 0)
    return f"+{p:.2f}%" if p >= 0 else f"{p:.2f}%"


def chg_color(d: dict) -> str:
    if d.get("error"): return "#7A92A8"
    return "#00E8A0" if d.get("chg_pct", 0) >= 0 else "#FF3D60"


def rsi_signal(rsi: float) -> tuple[str, str]:
    """Return (label, color) for an RSI value."""
    if rsi >= 70: return "Overbought", "#FF3D60"
    if rsi <= 30: return "Oversold",   "#00E8A0"
    return "Neutral", "#7A92A8"
