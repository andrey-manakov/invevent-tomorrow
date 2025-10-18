from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional, Tuple

from .. import db
from . import plans, timeutil


def create_share_token(sharer_id: int, plan_id: int, ttl_hours: int) -> str:
    conn = db.get_connection()
    token = secrets.token_urlsafe(8)
    expires_at = timeutil.utc_datetime_to_iso(timeutil.utc_now() + timedelta(hours=ttl_hours))
    conn.execute(
        """
        INSERT INTO share_tokens (token, sharer_id, plan_id, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (token, sharer_id, plan_id, expires_at),
    )
    conn.commit()
    return token


def redeem_token(token: str, redeemer_id: int) -> Optional[Tuple[dict, int]]:
    conn = db.get_connection()
    row = conn.execute(
        "SELECT * FROM share_tokens WHERE token = ?",
        (token,),
    ).fetchone()
    if not row:
        return None
    if row["redeemed_by"] is not None:
        return None
    if not timeutil.is_future(row["expires_at"]):
        return None

    plan = plans.get_plan(row["plan_id"])
    if not plan or plan["author_id"] != row["sharer_id"]:
        return None
    if not timeutil.is_future(plan["time_utc"]):
        return None

    now_iso = timeutil.utc_now_iso()
    conn.execute(
        "UPDATE share_tokens SET redeemed_by = ?, used_at = ? WHERE token = ?",
        (redeemer_id, now_iso, token),
    )
    conn.commit()
    return plan, row["sharer_id"]
