"""
db/ops.py — All CRUD operations.
FIX: _conn() context manager ensures connections always closed.
FIX: add_watch() correctly distinguishes inserted vs duplicate (rowcount check).
FIX: _sanitise_result() now handles numpy scalar types properly.
FIX: get_stats() returns safe zero-filled dict when avg_conf is None.
FIX: Retry logic on OperationalError (database is locked).
"""
from __future__ import annotations
import json
import time
import logging
from contextlib import contextmanager
from typing import Optional

from db.schema import get_conn

log = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 0.15  # seconds


@contextmanager
def _conn():
    """Open a connection and guarantee it is closed on exit."""
    c = get_conn()
    try:
        yield c
    finally:
        c.close()


def _retry_write(fn):
    """Decorator: retry DB writes up to _MAX_RETRIES times on lock errors."""
    import functools
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        for attempt in range(_MAX_RETRIES):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if "locked" in str(e).lower() and attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY)
                    continue
                raise
    return wrapper


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user(username: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE username=?", (username.lower(),)
        ).fetchone()
    return dict(row) if row else None


@_retry_write
def create_user(username: str, pw_hash: str, email: str = "", role: str = "user") -> bool:
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO users (username,password_hash,email,role) VALUES (?,?,?,?)",
                (username.lower(), pw_hash, email, role),
            )
            uid = c.execute(
                "SELECT id FROM users WHERE username=?", (username.lower(),)
            ).fetchone()["id"]
            c.execute(
                "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (uid,)
            )
            c.commit()
        return True
    except Exception as e:
        log.warning("create_user failed: %s", e)
        return False


@_retry_write
def touch_login(user_id: int) -> None:
    with _conn() as c:
        c.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user_id,))
        c.commit()


@_retry_write
def set_password(user_id: int, pw_hash: str) -> None:
    with _conn() as c:
        c.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, user_id))
        c.commit()


# ── ANALYSIS HISTORY ──────────────────────────────────────────────────────────

def _sanitise_result(result: dict) -> dict:
    """Strip non-JSON-serialisable fields (DataFrames, numpy scalars)."""
    import numpy as np
    import pandas as pd

    clean: dict = {}
    for k, v in result.items():
        if isinstance(v, pd.DataFrame):
            clean[k] = v.to_dict(orient="records") if not v.empty else []
        elif isinstance(v, (np.integer,)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating,)):
            clean[k] = float(v)
        elif isinstance(v, np.ndarray):
            clean[k] = v.tolist()
        else:
            clean[k] = v
    return clean


@_retry_write
def save_analysis(user_id: int, ticker: str, headline: str, result: dict) -> bool:
    """Save analysis result. Returns True on success, False on failure."""
    try:
        safe = _sanitise_result(result)
        with _conn() as c:
            c.execute(
                """INSERT INTO analysis_history
                   (user_id,ticker,headline,polarity,category,confidence,relevance_score,
                    event_type,is_rumour,credibility,ripple_count,result_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    user_id, ticker, headline,
                    result.get("polarity", 0),
                    result.get("category", "NEUTRAL"),
                    result.get("confidence", 0),
                    result.get("relevance_score", 0),
                    result.get("event_type", "General News"),
                    1 if result.get("is_rumour") else 0,
                    result.get("credibility", 1),
                    len(result.get("ripple_tree", [])),
                    json.dumps(safe, default=str),
                ),
            )
            c.commit()
        return True
    except Exception as e:
        log.error("save_analysis failed: %s", e)
        return False


def get_history(user_id: int, limit: int = 150) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM analysis_history WHERE user_id=? ORDER BY analyzed_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


@_retry_write
def delete_analysis(item_id: int, user_id: int) -> None:
    with _conn() as c:
        c.execute(
            "DELETE FROM analysis_history WHERE id=? AND user_id=?", (item_id, user_id)
        )
        c.commit()


@_retry_write
def clear_history(user_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM analysis_history WHERE user_id=?", (user_id,))
        c.commit()


def get_stats(user_id: int) -> dict:
    """FIX: Always returns a safe dict even when avg_conf is None."""
    with _conn() as c:
        row = c.execute(
            """SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN category IN ('POSITIVE','STRONG_POSITIVE') THEN 1 ELSE 0 END) AS positive,
                SUM(CASE WHEN category IN ('NEGATIVE','STRONG_NEGATIVE') THEN 1 ELSE 0 END) AS negative,
                SUM(CASE WHEN category='NEUTRAL' THEN 1 ELSE 0 END) AS neutral,
                AVG(confidence) AS avg_conf,
                COUNT(DISTINCT ticker) AS tickers
               FROM analysis_history WHERE user_id=?""",
            (user_id,),
        ).fetchone()
    if row is None:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "avg_conf": 0.0, "tickers": 0}
    d = dict(row)
    d["avg_conf"] = float(d.get("avg_conf") or 0.0)
    return d


# ── WATCHLIST ─────────────────────────────────────────────────────────────────

def get_watchlist(user_id: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM watchlist WHERE user_id=? ORDER BY added_at DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


@_retry_write
def add_watch(user_id: int, ticker: str, company: str = "", notes: str = "") -> bool:
    """FIX: Returns True only when a new row was actually inserted."""
    try:
        with _conn() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO watchlist (user_id,ticker,company_name,notes) VALUES (?,?,?,?)",
                (user_id, ticker.upper(), company, notes),
            )
            c.commit()
            return cur.rowcount > 0  # True = inserted, False = already existed
    except Exception as e:
        log.warning("add_watch failed: %s", e)
        return False


@_retry_write
def remove_watch(user_id: int, ticker: str) -> None:
    with _conn() as c:
        c.execute(
            "DELETE FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker.upper())
        )
        c.commit()


def in_watchlist(user_id: int, ticker: str) -> bool:
    if not user_id:
        return False
    with _conn() as c:
        r = c.execute(
            "SELECT id FROM watchlist WHERE user_id=? AND ticker=?",
            (user_id, ticker.upper()),
        ).fetchone()
    return r is not None


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_settings(user_id: int) -> dict:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM user_settings WHERE user_id=?", (user_id,)
        ).fetchone()
    return dict(row) if row else {
        "user_id": user_id,
        "default_ticker": "TSLA",
        "show_confidence": 1,
        "show_ripple": 1,
        "show_history": 1,
        "theme": "dark",
    }


@_retry_write
def save_settings(user_id: int, s: dict) -> None:
    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO user_settings
               (user_id,default_ticker,show_confidence,show_ripple,show_history,theme)
               VALUES (?,?,?,?,?,?)""",
            (
                user_id,
                s.get("default_ticker", "TSLA"),
                s.get("show_confidence", 1),
                s.get("show_ripple", 1),
                s.get("show_history", 1),
                s.get("theme", "dark"),
            ),
        )
        c.commit()


# ── PRICE ALERTS ─────────────────────────────────────────────────────────────

def get_active_alerts(user_id: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM price_alerts WHERE user_id=? AND triggered=0", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


@_retry_write
def add_alert(user_id: int, ticker: str, target: float, direction: str = "above") -> bool:
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO price_alerts (user_id,ticker,target_price,direction) VALUES (?,?,?,?)",
                (user_id, ticker.upper(), target, direction),
            )
            c.commit()
        return True
    except Exception as e:
        log.warning("add_alert failed: %s", e)
        return False


@_retry_write
def mark_alert_triggered(alert_id: int) -> None:
    with _conn() as c:
        c.execute("UPDATE price_alerts SET triggered=1 WHERE id=?", (alert_id,))
        c.commit()


@_retry_write
def delete_alert(alert_id: int, user_id: int) -> None:
    with _conn() as c:
        c.execute(
            "DELETE FROM price_alerts WHERE id=? AND user_id=?", (alert_id, user_id)
        )
        c.commit()
