from __future__ import annotations

from typing import Optional

from .services import timeutil


def format_plan_header(category: str, time_hm: str) -> str:
    return f"🗓 {category} • {time_hm} (tomorrow)"


def format_plan_body(
    category: str,
    time_hm: str,
    note: Optional[str] = None,
    location_label: Optional[str] = None,
) -> str:
    header = format_plan_header(category, time_hm)
    sections = [header]
    if note:
        sections.append(note)
    if location_label:
        sections.append(f"📍 {location_label}")
    return "\n".join(sections)


def format_plan_with_location(category: str, time_hm: str, note: Optional[str], location: Optional[str]) -> str:
    return format_plan_body(category, time_hm, note, location)


def format_share_message(link: str) -> str:
    return (
        "Share this link with a friend. The first person to open it will see your plan and "
        "you both will become friends!\n\n"
        f"{link}"
    )


def format_friend_join_confirmation() -> str:
    return "You're now friends! This plan has been added to your list for tomorrow."


def format_token_invalid() -> str:
    return "This share link is no longer valid. Ask your friend to share a fresh one."


def format_no_plans_message(owner: bool = False) -> str:
    if owner:
        return "No plans for tomorrow yet. Tap ➕ to create one!"
    return "Your friends have not shared plans for tomorrow yet."


def format_plan_summary(category: str, time_hm: str, note: Optional[str], location_label: Optional[str]) -> str:
    return format_plan_body(category, time_hm, note, location_label)


def format_plan_created() -> str:
    return "Plan saved for tomorrow!"


def format_plan_deleted() -> str:
    return "Plan deleted."


def format_plan_updated() -> str:
    return "Plan updated."


def format_settings_placeholder() -> str:
    return "Settings will be available soon."


def format_custom_time_prompt() -> str:
    return "Send a time in HH:MM (24h) for tomorrow."


def format_location_prompt() -> str:
    return "Send a location or type a place name. Use the menu to skip."


def format_note_prompt() -> str:
    return "Add a short note (120 chars) or skip."


def format_confirm_message(category: str, time_hm: str, note: Optional[str], location_label: Optional[str]) -> str:
    return "Review your plan for tomorrow:\n\n" + format_plan_body(category, time_hm, note, location_label)


def format_plan_joined_already() -> str:
    return "You already joined this plan."


def format_plan_not_found() -> str:
    return "Plan not found or already expired."


def format_share_token_created() -> str:
    return "Link ready! Share it with one friend to add them."


def format_friend_list_header() -> str:
    tomorrow = timeutil.tomorrow_local().strftime("%Y-%m-%d")
    return f"Plans for {tomorrow}"
