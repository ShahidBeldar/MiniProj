"""
db/schema.py — DDL: table creation, indexes, and user seeding.
Passwords for default accounts are read from environment variables;
hardcoded fallbacks are only used in development (FI_DEV_MODE=1).
"""
from __future__ import annotations
import os
import sqlite3


# ── PATH ──────────────────────────────────────────────────────────────────────

def _db_path() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    d = os.path.join(root, "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "finance_impact.db")


def get_conn() -> sqlite3.Connection:
    c = sqlite3.connect(_db_path(), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


# ── DDL ───────────────────────────────────────────────────────────────────────

def init_db() -> None:
    c = get_conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            email        TEXT    DEFAULT '',
            role         TEXT    DEFAULT 'user',
            created_at   TEXT    DEFAULT (datetime('now')),
            last_login   TEXT
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            ticker       TEXT    NOT NULL,
            company_name TEXT    DEFAULT '',
            notes        TEXT    DEFAULT '',
            added_at     TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, ticker),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id          INTEGER PRIMARY KEY,
            default_ticker   TEXT    DEFAULT 'TSLA',
            show_confidence  INTEGER DEFAULT 1,
            show_ripple      INTEGER DEFAULT 1,
            show_history     INTEGER DEFAULT 1,
            theme            TEXT    DEFAULT 'dark',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS price_alerts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            ticker       TEXT    NOT NULL,
            target_price REAL    NOT NULL,
            direction    TEXT    DEFAULT 'above',
            triggered    INTEGER DEFAULT 0,
            created_at   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Indexes for common query patterns
        CREATE INDEX IF NOT EXISTS idx_history_user
            ON analysis_history(user_id, analyzed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_watchlist_user
            ON watchlist(user_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_user
            ON price_alerts(user_id, triggered);
    """)
    c.commit()
    c.close()


# ── SEED USERS ────────────────────────────────────────────────────────────────

def seed_users() -> None:
    import bcrypt
    from db.ops import get_user, create_user

    dev_mode = os.environ.get("FI_DEV_MODE", "0") == "1"

    defaults = [
        (
            "admin",
            os.environ.get("FI_ADMIN_PASSWORD", "admin123" if dev_mode else None),
            "admin@fi.io",
            "admin",
        ),
        (
            "demo",
            os.environ.get("FI_DEMO_PASSWORD", "demo1234" if dev_mode else None),
            "demo@fi.io",
            "user",
        ),
        (
            "guest",
            os.environ.get("FI_GUEST_PASSWORD", "guest123" if dev_mode else None),
            "",
            "user",
        ),
    ]

    for uname, pwd, email, role in defaults:
        if pwd is None:
            continue  # skip if no password configured outside dev mode
        if not get_user(uname):
            h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            create_user(uname, h, email, role)
