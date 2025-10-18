from __future__ import annotations

from datetime import datetime, timedelta, timezone


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def local_tzinfo():
    return datetime.now().astimezone().tzinfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().strftime(ISO_FORMAT)


def tomorrow_local() -> datetime:
    now_local = datetime.now().astimezone()
    tomorrow = (now_local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return tomorrow


def tomorrow_ymd() -> str:
    return tomorrow_local().strftime("%Y-%m-%d")


def parse_time_hm(value: str) -> datetime:
    try:
        hour, minute = map(int, value.split(":"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Time must be in HH:MM format") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Invalid time provided")
    tzinfo = local_tzinfo()
    tomorrow_date = tomorrow_local().date()
    return datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, hour, minute, tzinfo=tzinfo)


def local_datetime_from_date(date_ymd: str, time_hm: str) -> datetime:
    year, month, day = map(int, date_ymd.split("-"))
    hour, minute = map(int, time_hm.split(":"))
    tzinfo = local_tzinfo()
    return datetime(year, month, day, hour, minute, tzinfo=tzinfo)


def local_to_utc_iso(local_dt: datetime) -> str:
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=local_tzinfo())
    return local_dt.astimezone(timezone.utc).strftime(ISO_FORMAT)


def utc_iso_to_datetime(value: str) -> datetime:
    return datetime.strptime(value, ISO_FORMAT).astimezone(timezone.utc)


def utc_datetime_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(ISO_FORMAT)


def is_future(utc_iso: str) -> bool:
    dt = utc_iso_to_datetime(utc_iso)
    return dt > utc_now()


def display_time_from_utc_iso(utc_iso: str) -> str:
    dt = utc_iso_to_datetime(utc_iso)
    local_dt = dt.astimezone(local_tzinfo())
    return local_dt.strftime("%H:%M")
