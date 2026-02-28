"""
db/ops.py — All CRUD operations. Imports db.schema for connection.
"""
from __future__ import annotations
import json
from typing import Optional
from db.schema import get_conn


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user(username: str) -> Optional[dict]:
    c = get_conn()
    row = c.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone()
    c.close()
    return dict(row) if row else None


def create_user(username: str, pw_hash: str, email: str = "", role: str = "user") -> bool:
    try:
        c = get_conn()
        c.execute(
            "INSERT INTO users (username,password_hash,email,role) VALUES (?,?,?,?)",
            (username.lower(), pw_hash, email, role),
        )
        uid = c.execute("SELECT id FROM users WHERE username=?", (username.lower(),)).fetchone()["id"]
        c.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (uid,))
        c.commit()
        c.close()
        return True
    except Exception:
        return False


def touch_login(user_id: int) -> None:
    c = get_conn()
    c.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user_id,))
    c.commit()
    c.close()


def set_password(user_id: int, pw_hash: str) -> None:
    c = get_conn()
    c.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, user_id))
    c.commit()
    c.close()


# ── ANALYSIS HISTORY ──────────────────────────────────────────────────────────

def _sanitise_result(result: dict) -> dict:
    """Strip non-JSON-serialisable fields (DataFrames) before storing."""
    import pandas as pd
    clean: dict = {}
    for k, v in result.items():
        if isinstance(v, pd.DataFrame):
            clean[k] = v.to_dict(orient="records") if not v.empty else []
        else:
            clean[k] = v
    return clean


def save_analysis(user_id: int, ticker: str, headline: str, result: dict) -> None:
    safe = _sanitise_result(result)
    c    = get_conn()
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
    c.close()


def get_history(user_id: int, limit: int = 150) -> list[dict]:
    c = get_conn()
    rows = c.execute(
        "SELECT * FROM analysis_history WHERE user_id=? ORDER BY analyzed_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def delete_analysis(item_id: int, user_id: int) -> None:
    c = get_conn()
    c.execute("DELETE FROM analysis_history WHERE id=? AND user_id=?", (item_id, user_id))
    c.commit()
    c.close()


def clear_history(user_id: int) -> None:
    c = get_conn()
    c.execute("DELETE FROM analysis_history WHERE user_id=?", (user_id,))
    c.commit()
    c.close()


def get_stats(user_id: int) -> dict:
    c   = get_conn()
    row = c.execute(
        """SELECT
            COUNT(*)                                                    AS total,
            SUM(CASE WHEN category IN ('POSITIVE','STRONG_POSITIVE') THEN 1 ELSE 0 END) AS positive,
            SUM(CASE WHEN category IN ('NEGATIVE','STRONG_NEGATIVE') THEN 1 ELSE 0 END) AS negative,
            SUM(CASE WHEN category='NEUTRAL'                         THEN 1 ELSE 0 END) AS neutral,
            AVG(confidence)                                            AS avg_conf,
            COUNT(DISTINCT ticker)                                     AS tickers
        FROM analysis_history WHERE user_id=?""",
        (user_id,),
    ).fetchone()
    c.close()
    return dict(row) if row else {}


# ── WATCHLIST ─────────────────────────────────────────────────────────────────

def get_watchlist(user_id: int) -> list[dict]:
    c    = get_conn()
    rows = c.execute(
        "SELECT * FROM watchlist WHERE user_id=? ORDER BY added_at DESC",
        (user_id,),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def add_watch(user_id: int, ticker: str, company: str = "", notes: str = "") -> bool:
    try:
        c = get_conn()
        c.execute(
            "INSERT OR IGNORE INTO watchlist (user_id,ticker,company_name,notes) VALUES (?,?,?,?)",
            (user_id, ticker.upper(), company, notes),
        )
        c.commit()
        c.close()
        return True
    except Exception:
        return False


def remove_watch(user_id: int, ticker: str) -> None:
    c = get_conn()
    c.execute("DELETE FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker.upper()))
    c.commit()
    c.close()


def in_watchlist(user_id: int, ticker: str) -> bool:
    c = get_conn()
    r = c.execute(
        "SELECT id FROM watchlist WHERE user_id=? AND ticker=?",
        (user_id, ticker.upper()),
    ).fetchone()
    c.close()
    return r is not None


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_settings(user_id: int) -> dict:
    c   = get_conn()
    row = c.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
    c.close()
    return dict(row) if row else {
        "user_id": user_id, "default_ticker": "TSLA",
        "show_confidence": 1, "show_ripple": 1, "show_history": 1,
    }


def save_settings(user_id: int, s: dict) -> None:
    c = get_conn()
    c.execute(
        """INSERT OR REPLACE INTO user_settings
           (user_id,default_ticker,show_confidence,show_ripple,show_history)
           VALUES (?,?,?,?,?)""",
        (
            user_id,
            s.get("default_ticker", "TSLA"),
            s.get("show_confidence", 1),
            s.get("show_ripple",     1),
            s.get("show_history",    1),
        ),
    )
    c.commit()
    c.close()
