"""
db/schema.py — DDL: table creation + user seeding.
"""
from __future__ import annotations
import sqlite3, os


def _db_path() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    d    = os.path.join(root, "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "finance_impact.db")


def get_conn() -> sqlite3.Connection:
    c = sqlite3.connect(_db_path(), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init_db() -> None:
    c = get_conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email         TEXT DEFAULT '',
            role          TEXT DEFAULT 'user',
            created_at    TEXT DEFAULT (datetime('now')),
            last_login    TEXT
        );
        CREATE TABLE IF NOT EXISTS analysis_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            ticker          TEXT NOT NULL,
            headline        TEXT NOT NULL,
            polarity        REAL    DEFAULT 0,
            category        TEXT    DEFAULT 'NEUTRAL',
            confidence      REAL    DEFAULT 0,
            relevance_score REAL    DEFAULT 0,
            event_type      TEXT    DEFAULT 'General News',
            is_rumour       INTEGER DEFAULT 0,
            credibility     REAL    DEFAULT 1,
            ripple_count    INTEGER DEFAULT 0,
            result_json     TEXT,
            analyzed_at     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            ticker       TEXT NOT NULL,
            company_name TEXT    DEFAULT '',
            notes        TEXT    DEFAULT '',
            added_at     TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, ticker),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id         INTEGER PRIMARY KEY,
            default_ticker  TEXT    DEFAULT 'TSLA',
            show_confidence INTEGER DEFAULT 1,
            show_ripple     INTEGER DEFAULT 1,
            show_history    INTEGER DEFAULT 1,
            theme           TEXT    DEFAULT 'dark',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    c.commit()
    c.close()


def seed_users() -> None:
    import bcrypt
    from db.ops import get_user, create_user
    defaults = [
        ("admin", "admin123", "admin@fi.io", "admin"),
        ("demo",  "demo1234", "demo@fi.io",  "user"),
        ("guest", "guest123", "",            "user"),
    ]
    for uname, pwd, email, role in defaults:
        if not get_user(uname):
            h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            create_user(uname, h, email, role)
