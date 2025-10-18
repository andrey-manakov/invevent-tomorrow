from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock
from typing import Iterable, Optional

_connection: Optional[sqlite3.Connection] = None
_lock = RLock()


SCHEMA_STATEMENTS: Iterable[str] = (
    "PRAGMA foreign_keys = ON;",
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS friendships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_a_id INTEGER NOT NULL,
        user_b_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACCEPTED',
        created_at TEXT NOT NULL,
        UNIQUE(user_a_id, user_b_id),
        CHECK(user_a_id < user_b_id),
        FOREIGN KEY(user_a_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(user_b_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_id INTEGER NOT NULL,
        date_ymd TEXT NOT NULL,
        category TEXT NOT NULL,
        time_hm TEXT NOT NULL,
        time_utc TEXT NOT NULL,
        location_lat REAL,
        location_lon REAL,
        location_label TEXT,
        note TEXT,
        base_plan_id INTEGER,
        visibility TEXT NOT NULL DEFAULT 'FRIENDS_ONLY',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(base_plan_id) REFERENCES plans(id) ON DELETE SET NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_plans_author_date ON plans(author_id, date_ymd);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_plans_time_utc ON plans(time_utc);
    """,
    """
    CREATE TABLE IF NOT EXISTS share_tokens (
        token TEXT PRIMARY KEY,
        sharer_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        expires_at TEXT NOT NULL,
        redeemed_by INTEGER,
        used_at TEXT,
        FOREIGN KEY(sharer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE,
        FOREIGN KEY(redeemed_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_share_tokens_plan ON share_tokens(plan_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_friendships_pair ON friendships(user_a_id, user_b_id);
    """
)


class DatabaseNotInitializedError(RuntimeError):
    pass


def init_db(db_path: Path) -> sqlite3.Connection:
    global _connection
    with _lock:
        if _connection is not None:
            return _connection

        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        with conn:
            for statement in SCHEMA_STATEMENTS:
                conn.executescript(statement)

        _connection = conn
        return conn


def get_connection() -> sqlite3.Connection:
    if _connection is None:
        raise DatabaseNotInitializedError('Database not initialized. Call init_db first.')
    return _connection


def close_connection() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None
