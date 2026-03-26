"""
core/stocks.py — yFinance wrapper.
FIX: Exception messages sanitised — internal paths never reach the UI.
FIX: Long-window indicators (MA200 etc.) gated on DataFrame length.
FIX: Intraday (1d/5d) empty DataFrames fall back to longer period automatically.
FIX: Index prices fetched in parallel via ThreadPoolExecutor.
Pure Python — no Streamlit imports. Callers wrap with @st.cache_data.
"""
from __future__ import annotations
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed


# ── TICKER MAPPINGS ───────────────────────────────────────────────────────────

_INDIAN: dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "WIPRO":    "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK":"ICICIBANK.NS",
    "BAJFINANCE":"BAJFINANCE.NS",
}

MARKET_INDICES: dict[str, str] = {
    "S&P 500":   "^GSPC",
    "NASDAQ":    "^IXIC",
    "DOW JONES": "^DJI",
    "VIX":       "^VIX",
    "NIFTY 50":  "^NSEI",
    "SENSEX":    "^BSESN",
    "FTSE 100":  "^FTSE",
    "NIKKEI 225":"^N225",
    "HANG SENG": "^HSI",
    "DAX":       "^GDAXI",
}

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

ALL_TICKERS = list(_INDIAN.keys()) + ["TSLA", "AAPL", "GOOGL", "MSFT", "NVDA", "AMZN"]

# Intraday periods and their fallback equivalents
_INTRADAY_FALLBACK: dict[str, str] = {
    "1d": "5d",
    "5d": "1mo",
}


def _yt(ticker: str) -> str:
    return _INDIAN.get(ticker.upper(), ticker.upper())


# ── PRICE ─────────────────────────────────────────────────────────────────────

def get_price(ticker: str) -> dict:
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
    except Exception:
        return {
            "ticker":   ticker,
            "price":    0.0,
            "change":   0.0,
            "chg_pct":  0.0,
            "currency": "$",
            "error":    True,
            "msg":      "Price data unavailable",
        }


def _fetch_index_price(name: str, sym: str) -> tuple[str, dict]:
    try:
        info = yf.Ticker(sym).fast_info
        p    = round(float(info.last_price), 2)
        prev = round(float(info.previous_close), 2)
        chg  = round(p - prev, 2)
        chgp = round((chg / prev) * 100, 2) if prev else 0.0
        return name, {"symbol": sym, "price": p, "change": chg, "chg_pct": chgp, "error": False}
    except Exception:
        return name, {"symbol": sym, "price": 0.0, "change": 0.0, "chg_pct": 0.0,
                      "error": True, "msg": "Index data unavailable"}


def get_index_prices() -> dict[str, dict]:
    """Fetch all market indices in parallel."""
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_index_price, n, s): n for n, s in MARKET_INDICES.items()}
        for future in as_completed(futures):
            try:
                name, data = future.result(timeout=8)
                out[name] = data
            except Exception:
                n = futures[future]
                out[n] = {"symbol": MARKET_INDICES.get(n, ""), "price": 0.0,
                          "change": 0.0, "chg_pct": 0.0, "error": True,
                          "msg": "Index data unavailable"}
    # Preserve original order
    return {n: out[n] for n in MARKET_INDICES if n in out}


# ── OHLCV ─────────────────────────────────────────────────────────────────────

def _download(sym: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(sym, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if df is None or (hasattr(df, "empty") and df.empty):
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[0]) for c in df.columns]
    rename: dict[str, str] = {}
    for c in df.columns:
        cl = str(c).lower()
        if   cl == "open":        rename[c] = "Open"
        elif cl == "high":        rename[c] = "High"
        elif cl == "low":         rename[c] = "Low"
        elif cl == "close":       rename[c] = "Close"
        elif "vol" in cl:         rename[c] = "Volume"
    df = df.rename(columns=rename)
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    return df[keep].dropna(subset=["Close"])


def get_ohlcv(ticker: str, period_label: str = "3 Months") -> pd.DataFrame:
    """
    Fetch OHLCV for the given period_label key.
    For intraday periods (1d/5d) automatically falls back to a longer period
    if the primary fetch returns empty (e.g. weekend / holiday).
    """
    period, interval = PERIOD_OPTIONS.get(period_label, ("3mo", "1d"))
    sym = _yt(ticker)
    df = _download(sym, period, interval)

    # Intraday fallback
    if df.empty and period in _INTRADAY_FALLBACK:
        fallback_p = _INTRADAY_FALLBACK[period]
        fallback_i = PERIOD_OPTIONS.get(
            next((k for k, v in PERIOD_OPTIONS.items() if v[0] == fallback_p), "1 Month"),
            ("1mo", "1d")
        )[1]
        df = _download(sym, fallback_p, fallback_i)

    return df


def get_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """Shim: maps days → period_label → get_ohlcv."""
    if days <= 1:    label = "1 Day"
    elif days <= 5:  label = "5 Days"
    elif days <= 31: label = "1 Month"
    elif days <= 92: label = "3 Months"
    elif days <= 183:label = "6 Months"
    else:            label = "1 Year"
    return get_ohlcv(ticker, label)


# ── TECHNICAL INDICATORS ──────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach technical indicators to an OHLCV DataFrame.
    FIX: Long-window MAs (MA50, MA200) only computed when sufficient rows exist.
    Adds: MA20, MA50, MA200, EMA12, EMA26, MACD, MACD_Signal, MACD_Hist,
          BB_Upper, BB_Mid, BB_Lower, RSI, ATR, VWAP.
    """
    if df.empty or "Close" not in df.columns:
        return df

    df = df.copy()
    n = len(df)
    c = df["Close"]
    h = df["High"]   if "High"   in df.columns else c
    lo= df["Low"]    if "Low"    in df.columns else c
    v = df["Volume"] if "Volume" in df.columns else pd.Series(0, index=df.index)

    # Moving averages — gated on data length
    df["MA20"]  = c.rolling(min(20, n),  min_periods=1).mean().round(4)
    df["MA50"]  = c.rolling(min(50, n),  min_periods=1).mean().round(4) if n >= 10 else np.nan
    df["MA200"] = c.rolling(min(200, n), min_periods=1).mean().round(4) if n >= 20 else np.nan

    # EMA & MACD
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["EMA12"]       = ema12.round(4)
    df["EMA26"]       = ema26.round(4)
    df["MACD"]        = (ema12 - ema26).round(4)
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean().round(4)
    df["MACD_Hist"]   = (df["MACD"] - df["MACD_Signal"]).round(4)

    # Bollinger Bands (20-period, 2σ)
    std20 = c.rolling(min(20, n), min_periods=1).std()
    df["BB_Mid"]   = df["MA20"]
    df["BB_Upper"] = (df["MA20"] + 2 * std20).round(4)
    df["BB_Lower"] = (df["MA20"] - 2 * std20).round(4)

    # RSI (14)
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = (100 - 100 / (1 + rs)).round(2)

    # ATR (14)
    tr = pd.concat(
        [h - lo, (h - c.shift()).abs(), (lo - c.shift()).abs()], axis=1
    ).max(axis=1)
    df["ATR"] = tr.rolling(14, min_periods=1).mean().round(4)

    # VWAP (cumulative approximation)
    typical = (h + lo + c) / 3
    cum_tp_v = (typical * v).cumsum()
    cum_v = v.cumsum().replace(0, np.nan)
    df["VWAP"] = (cum_tp_v / cum_v).round(4)

    return df


def get_ohlcv_with_indicators(ticker: str, period_label: str = "3 Months") -> pd.DataFrame:
    df = get_ohlcv(ticker, period_label)
    return add_indicators(df) if not df.empty else df


def get_multi_ticker(tickers: list[str], period_label: str = "3 Months") -> dict[str, pd.DataFrame]:
    return {t: get_ohlcv_with_indicators(t, period_label) for t in tickers}


# ── COMPANY INFO ──────────────────────────────────────────────────────────────

def get_ticker_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(_yt(ticker)).info or {}
        mc = info.get("marketCap") or 0
        mc_s = (
            f"${mc/1e12:.2f}T" if mc >= 1e12 else
            f"${mc/1e9:.2f}B"  if mc >= 1e9  else
            f"${mc/1e6:.2f}M"  if mc >= 1e6  else "N/A"
        )
        return {
            "name":         info.get("longName") or info.get("shortName") or ticker,
            "sector":       info.get("sector",   "N/A"),
            "industry":     info.get("industry", "N/A"),
            "market_cap":   mc_s,
            "pe_ratio":     round(float(info.get("trailingPE")    or 0), 2),
            "eps":          round(float(info.get("trailingEps")   or 0), 2),
            "week52_high":  round(float(info.get("fiftyTwoWeekHigh") or 0), 2),
            "week52_low":   round(float(info.get("fiftyTwoWeekLow")  or 0), 2),
            "avg_volume":   info.get("averageVolume") or 0,
            "beta":         round(float(info.get("beta")           or 0), 2),
            "dividend_yield": round(float(info.get("dividendYield") or 0) * 100, 2),
            "description":  (info.get("longBusinessSummary") or "")[:400],
            "error":        False,
        }
    except Exception:
        return {"name": ticker, "error": True, "msg": "Company info unavailable"}


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────

def fmt_price(d: dict) -> str:
    if d.get("error"):
        return "N/A"
    return f"{d.get('currency','$')}{d.get('price', 0):,.2f}"


def fmt_change(d: dict) -> str:
    if d.get("error"):
        return "N/A"
    p = d.get("chg_pct", 0)
    return f"+{p:.2f}%" if p >= 0 else f"{p:.2f}%"


def chg_color(d: dict) -> str:
    if d.get("error"):
        return "#7A92A8"
    return "#00E8A0" if d.get("chg_pct", 0) >= 0 else "#FF3D60"


def rsi_signal(rsi: float) -> tuple[str, str]:
    if rsi >= 70: return "Overbought", "#FF3D60"
    if rsi <= 30: return "Oversold",   "#00E8A0"
    return "Neutral", "#7A92A8"
