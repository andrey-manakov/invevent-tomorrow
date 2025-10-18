from __future__ import annotations

from typing import List, Optional

from telebot.types import User as TgUser

from .. import db
from . import timeutil


def ensure_user(tg_user: TgUser) -> int:
    conn = db.get_connection()
    existing = conn.execute("SELECT id FROM users WHERE tg_id = ?", (tg_user.id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE users SET username = ?, first_name = ?, last_name = ?, updated_at = ? WHERE id = ?",
            (
                tg_user.username,
                tg_user.first_name,
                tg_user.last_name,
                timeutil.utc_now_iso(),
                existing["id"],
            ),
        )
        conn.commit()
        return existing["id"]

    now_iso = timeutil.utc_now_iso()
    cursor = conn.execute(
        """
        INSERT INTO users (tg_id, username, first_name, last_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tg_user.id,
            tg_user.username,
            tg_user.first_name,
            tg_user.last_name,
            now_iso,
            now_iso,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_user_by_id(user_id: int) -> Optional[int]:
    conn = db.get_connection()
    row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["id"] if row else None


def are_friends(user_id: int, other_id: int) -> bool:
    if user_id == other_id:
        return True
    a, b = sorted((user_id, other_id))
    conn = db.get_connection()
    row = conn.execute(
        "SELECT 1 FROM friendships WHERE user_a_id = ? AND user_b_id = ? AND status = 'ACCEPTED'",
        (a, b),
    ).fetchone()
    return bool(row)


def add_friendship(user_id: int, other_id: int) -> None:
    if user_id == other_id:
        return
    a, b = sorted((user_id, other_id))
    conn = db.get_connection()
    existing = conn.execute(
        "SELECT id FROM friendships WHERE user_a_id = ? AND user_b_id = ?",
        (a, b),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE friendships SET status = 'ACCEPTED' WHERE id = ?",
            (existing["id"],),
        )
        conn.commit()
        return

    now_iso = timeutil.utc_now_iso()
    conn.execute(
        """
        INSERT INTO friendships (user_a_id, user_b_id, status, created_at)
        VALUES (?, ?, 'ACCEPTED', ?)
        """,
        (a, b, now_iso),
    )
    conn.commit()


def list_friend_ids(user_id: int) -> List[int]:
    conn = db.get_connection()
    rows = conn.execute(
        """
        SELECT CASE WHEN user_a_id = ? THEN user_b_id ELSE user_a_id END AS friend_id
        FROM friendships
        WHERE (user_a_id = ? OR user_b_id = ?) AND status = 'ACCEPTED'
        """,
        (user_id, user_id, user_id),
    ).fetchall()
    return [row["friend_id"] for row in rows]
