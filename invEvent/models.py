from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class User:
    id: int
    tg_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Plan:
    id: int
    author_id: int
    date_ymd: str
    category: str
    time_hm: str
    time_utc: datetime
    location_lat: Optional[float]
    location_lon: Optional[float]
    location_label: Optional[str]
    note: Optional[str]
    base_plan_id: Optional[int]
    visibility: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ShareToken:
    token: str
    sharer_id: int
    plan_id: int
    expires_at: datetime
    redeemed_by: Optional[int]
    used_at: Optional[datetime]
