"""
db.py — SQLite setup and all DB operations.
"""

import sqlite3
import os
import json


def get_db_path() -> str:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "finance_impact.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email         TEXT,
            created_at    TEXT DEFAULT (datetime('now')),
            last_login    TEXT,
            role          TEXT DEFAULT 'user'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            ticker          TEXT NOT NULL,
            headline        TEXT NOT NULL,
            polarity        REAL,
            category        TEXT,
            confidence      REAL,
            relevance_score REAL,
            event_type      TEXT,
            is_rumour       INTEGER DEFAULT 0,
            credibility     REAL,
            ripple_count    INTEGER DEFAULT 0,
            result_json     TEXT,
            analyzed_at     TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            ticker       TEXT NOT NULL,
            company_name TEXT,
            added_at     TEXT DEFAULT (datetime('now')),
            notes        TEXT,
            UNIQUE(user_id, ticker),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id         INTEGER PRIMARY KEY,
            default_ticker  TEXT DEFAULT 'TSLA',
            show_confidence INTEGER DEFAULT 1,
            show_ripple     INTEGER DEFAULT 1,
            show_history    INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user_by_username(username: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username: str, password_hash: str, email: str = "", role: str = "user") -> bool:
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (username, password_hash, email, role) VALUES (?,?,?,?)",
            (username, password_hash, email, role)
        )
        user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if user:
            conn.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user["id"],))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def update_last_login(user_id: int):
    conn = get_conn()
    conn.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def update_user_password(user_id: int, new_hash: str):
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
    conn.commit()
    conn.close()


def seed_default_users():
    import bcrypt
    defaults = [
        ("admin", "admin123", "admin@financeimpact.io", "admin"),
        ("demo",  "demo1234", "demo@financeimpact.io",  "user"),
        ("guest", "guest123", "",                       "user"),
    ]
    for uname, pwd, email, role in defaults:
        if not get_user_by_username(uname):
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            create_user(uname, hashed, email, role)


# ── HISTORY ───────────────────────────────────────────────────────────────────

def save_analysis(user_id: int, ticker: str, headline: str, result: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO analysis_history
            (user_id, ticker, headline, polarity, category, confidence,
             relevance_score, event_type, is_rumour, credibility, ripple_count, result_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, ticker, headline,
        result.get("polarity", 0.0),
        result.get("category", "NEUTRAL"),
        result.get("confidence", 0.0),
        result.get("relevance_score", 0.0),
        result.get("event_type", "General"),
        1 if result.get("is_rumour", False) else 0,
        result.get("credibility", 1.0),
        len(result.get("ripple_tree", [])),
        json.dumps(result, default=str),
    ))
    conn.commit()
    conn.close()


def get_user_history(user_id: int, limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM analysis_history WHERE user_id=? ORDER BY analyzed_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_history_item(item_id: int, user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM analysis_history WHERE id=? AND user_id=?", (item_id, user_id))
    conn.commit()
    conn.close()


def clear_user_history(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM analysis_history WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_user_stats(user_id: int) -> dict:
    conn = get_conn()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN category IN ('POSITIVE','STRONG_POSITIVE') THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN category IN ('NEGATIVE','STRONG_NEGATIVE') THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN category = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral,
            AVG(confidence) as avg_confidence,
            COUNT(DISTINCT ticker) as unique_tickers
        FROM analysis_history WHERE user_id=?
    """, (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ── WATCHLIST ─────────────────────────────────────────────────────────────────

def get_watchlist(user_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM watchlist WHERE user_id=? ORDER BY added_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_to_watchlist(user_id: int, ticker: str, company_name: str, notes: str = "") -> bool:
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, ticker, company_name, notes) VALUES (?,?,?,?)",
            (user_id, ticker.upper(), company_name, notes),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def remove_from_watchlist(user_id: int, ticker: str):
    conn = get_conn()
    conn.execute("DELETE FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker.upper()))
    conn.commit()
    conn.close()


def is_in_watchlist(user_id: int, ticker: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker.upper())
    ).fetchone()
    conn.close()
    return row is not None


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_user_settings(user_id: int) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "user_id":        user_id,
        "default_ticker": "TSLA",
        "show_confidence": 1,
        "show_ripple":     1,
        "show_history":    1,
    }


def update_user_settings(user_id: int, settings: dict):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO user_settings
            (user_id, default_ticker, show_confidence, show_ripple, show_history)
        VALUES (?,?,?,?,?)
    """, (
        user_id,
        settings.get("default_ticker", "TSLA"),
        settings.get("show_confidence", 1),
        settings.get("show_ripple", 1),
        settings.get("show_history", 1),
    ))
    conn.commit()
    conn.close()
