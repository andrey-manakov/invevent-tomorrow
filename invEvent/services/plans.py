from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .. import db
from . import timeutil


@dataclass(slots=True)
class PlanData:
    category: str
    time_hm: str
    time_utc: str
    date_ymd: str
    note: Optional[str]
    location_lat: Optional[float]
    location_lon: Optional[float]
    location_label: Optional[str]
    base_plan_id: Optional[int]


def _row_to_dict(row) -> Dict:
    return dict(row) if row else None


def create_plan(
    author_id: int,
    category: str,
    time_hm: str,
    note: Optional[str],
    location_lat: Optional[float],
    location_lon: Optional[float],
    location_label: Optional[str],
    base_plan_id: Optional[int] = None,
    date_ymd: Optional[str] = None,
) -> int:
    if date_ymd:
        local_dt = timeutil.local_datetime_from_date(date_ymd, time_hm)
    else:
        local_dt = timeutil.parse_time_hm(time_hm)
    plan = PlanData(
        category=category,
        time_hm=local_dt.strftime("%H:%M"),
        time_utc=timeutil.local_to_utc_iso(local_dt),
        date_ymd=date_ymd or timeutil.tomorrow_ymd(),
        note=note,
        location_lat=location_lat,
        location_lon=location_lon,
        location_label=location_label,
        base_plan_id=base_plan_id,
    )
    conn = db.get_connection()
    cursor = conn.execute(
        """
        INSERT INTO plans (
            author_id, date_ymd, category, time_hm, time_utc,
            location_lat, location_lon, location_label, note, base_plan_id, visibility, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'FRIENDS_ONLY', ?, ?)
        """,
        (
            author_id,
            plan.date_ymd,
            plan.category,
            plan.time_hm,
            plan.time_utc,
            plan.location_lat,
            plan.location_lon,
            plan.location_label,
            plan.note,
            plan.base_plan_id,
            timeutil.utc_now_iso(),
            timeutil.utc_now_iso(),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def update_plan(
    plan_id: int,
    author_id: int,
    category: str,
    time_hm: str,
    note: Optional[str],
    location_lat: Optional[float],
    location_lon: Optional[float],
    location_label: Optional[str],
) -> bool:
    local_dt = timeutil.parse_time_hm(time_hm)
    conn = db.get_connection()
    result = conn.execute(
        """
        UPDATE plans SET category = ?, time_hm = ?, time_utc = ?, note = ?,
            location_lat = ?, location_lon = ?, location_label = ?, updated_at = ?
        WHERE id = ? AND author_id = ?
        """,
        (
            category,
            local_dt.strftime("%H:%M"),
            timeutil.local_to_utc_iso(local_dt),
            note,
            location_lat,
            location_lon,
            location_label,
            timeutil.utc_now_iso(),
            plan_id,
            author_id,
        ),
    )
    conn.commit()
    return result.rowcount > 0


def delete_plan(plan_id: int, author_id: int) -> bool:
    conn = db.get_connection()
    result = conn.execute("DELETE FROM plans WHERE id = ? AND author_id = ?", (plan_id, author_id))
    conn.commit()
    return result.rowcount > 0


def get_plan(plan_id: int) -> Optional[Dict]:
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    return _row_to_dict(row)


def list_user_plans(author_id: int) -> List[Dict]:
    conn = db.get_connection()
    rows = conn.execute(
        """
        SELECT * FROM plans
        WHERE author_id = ? AND date_ymd = ?
        ORDER BY time_utc ASC
        """,
        (author_id, timeutil.tomorrow_ymd()),
    ).fetchall()
    plans = [dict(row) for row in rows if timeutil.is_future(row["time_utc"])]
    return plans


def list_friend_plans(user_id: int, friend_ids: Iterable[int]) -> List[Dict]:
    if not friend_ids:
        return []
    placeholders = ",".join(["?"] * len(friend_ids))
    conn = db.get_connection()
    query = f"""
        SELECT * FROM plans
        WHERE author_id IN ({placeholders}) AND date_ymd = ?
        ORDER BY time_utc ASC
    """
    rows = conn.execute(query, (*friend_ids, timeutil.tomorrow_ymd())).fetchall()
    return [dict(row) for row in rows if timeutil.is_future(row["time_utc"]) and row["author_id"] != user_id]


def has_joined_plan(user_id: int, base_plan_id: int, date_ymd: str) -> bool:
    conn = db.get_connection()
    row = conn.execute(
        "SELECT 1 FROM plans WHERE author_id = ? AND base_plan_id = ? AND date_ymd = ?",
        (user_id, base_plan_id, date_ymd),
    ).fetchone()
    return bool(row)
