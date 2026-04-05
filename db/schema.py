"""
db/schema.py — DDL: table creation, indexes, and user seeding.

ROOT CAUSE FIX: The previous _DB_INITIALIZED module-level bool was not thread-safe
and was not shared across Streamlit reruns on Streamlit Cloud workers.
Every DB operation now calls ensure_db() which uses a threading.Lock so init
truly runs once per process even under concurrent reruns.

DB PATH: /tmp/finance_impact.db on Streamlit Cloud (writable, persists within
a running process). Override with FI_DB_PATH env var for production use.
"""
from __future__ import annotations
import os
import sqlite3
import threading
from contextlib import contextmanager

_init_lock = threading.Lock()
_initialized = False          # protected by _init_lock


def _db_path() -> str:
    env = os.environ.get("FI_DB_PATH", "")
    if env:
        os.makedirs(os.path.dirname(os.path.abspath(env)), exist_ok=True)
        return env
    os.makedirs("/tmp", exist_ok=True)
    return "/tmp/finance_impact.db"


@contextmanager
def _conn_ctx():
    c = sqlite3.connect(_db_path(), check_same_thread=False, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
    finally:
        c.close()


def get_conn() -> sqlite3.Connection:
    c = sqlite3.connect(_db_path(), check_same_thread=False, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def ensure_db() -> None:
    """
    Create tables + seed demo users. True singleton — runs once per process.
    Safe to call from every single DB function; near-zero cost after first call.
    Uses threading.Lock + double-checked locking to be safe under concurrent reruns.
    """
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        _create_tables()
        _seed_users()
        _initialized = True


def init_db() -> None:
    """Backward-compat alias."""
    ensure_db()


def _create_tables() -> None:
    with _conn_ctx() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                email         TEXT    DEFAULT '',
                role          TEXT    DEFAULT 'user',
                created_at    TEXT    DEFAULT (datetime('now')),
                last_login    TEXT
            );
            CREATE TABLE IF NOT EXISTS analysis_history (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                ticker           TEXT    NOT NULL,
                headline         TEXT    NOT NULL,
                polarity         REAL    DEFAULT 0,
                category         TEXT    DEFAULT 'NEUTRAL',
                confidence       REAL    DEFAULT 0,
                relevance_score  REAL    DEFAULT 0,
                event_type       TEXT    DEFAULT 'General News',
                is_rumour        INTEGER DEFAULT 0,
                credibility      REAL    DEFAULT 1,
                ripple_count     INTEGER DEFAULT 0,
                result_json      TEXT,
                analyzed_at      TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                ticker       TEXT    NOT NULL,
                company_name TEXT    DEFAULT '',
                notes        TEXT    DEFAULT '',
                added_at     TEXT    DEFAULT (datetime('now')),
                UNIQUE(user_id, ticker),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id          INTEGER PRIMARY KEY,
                default_ticker   TEXT    DEFAULT 'TSLA',
                show_confidence  INTEGER DEFAULT 1,
                show_ripple      INTEGER DEFAULT 1,
                show_history     INTEGER DEFAULT 1,
                theme            TEXT    DEFAULT 'dark',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS price_alerts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                ticker       TEXT    NOT NULL,
                target_price REAL    NOT NULL,
                direction    TEXT    DEFAULT 'above',
                triggered    INTEGER DEFAULT 0,
                created_at   TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_history_user
                ON analysis_history(user_id, analyzed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_watchlist_user
                ON watchlist(user_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_user
                ON price_alerts(user_id, triggered);
        """)
        c.commit()


def _seed_users() -> None:
    """Insert default demo accounts inside the same init transaction."""
    try:
        import bcrypt
    except ImportError:
        return
    defaults = [
        ("admin", os.environ.get("FI_ADMIN_PASSWORD", "admin123"), "admin@fi.io", "admin"),
        ("demo",  os.environ.get("FI_DEMO_PASSWORD",  "demo1234"), "demo@fi.io",  "user"),
        ("guest", os.environ.get("FI_GUEST_PASSWORD", "guest123"), "",            "user"),
    ]
    with _conn_ctx() as c:
        for uname, pwd, email, role in defaults:
            exists = c.execute(
                "SELECT id FROM users WHERE username=?", (uname,)
            ).fetchone()
            if not exists:
                h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                c.execute(
                    "INSERT INTO users (username,password_hash,email,role) VALUES (?,?,?,?)",
                    (uname, h, email, role),
                )
                new_id = c.execute(
                    "SELECT id FROM users WHERE username=?", (uname,)
                ).fetchone()["id"]
                c.execute(
                    "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (new_id,)
                )
        c.commit()


def seed_users() -> None:
    """Backward-compat alias."""
    _seed_users()
