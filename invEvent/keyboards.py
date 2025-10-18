from __future__ import annotations

from typing import Iterable, List, Optional

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORIES = [
    "Coffee",
    "Walk",
    "Gym",
    "Run",
    "Dinner",
    "Drinks",
    "Study",
    "Movie",
    "Work",
    "Other",
]

PRESET_TIMES = [
    "07:00",
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(text="➕ New plan for tomorrow", callback_data="menu:new_plan"),
        InlineKeyboardButton(text="👥 Friends' plans (tomorrow)", callback_data="menu:friends"),
        InlineKeyboardButton(text="📋 My plans (tomorrow)", callback_data="menu:mine"),
        InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings"),
    )
    return markup


def categories_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    buttons: List[InlineKeyboardButton] = []
    for category in CATEGORIES:
        buttons.append(InlineKeyboardButton(text=category, callback_data=f"cat:{category}"))
    markup.add(*buttons, row_width=2)
    markup.add(InlineKeyboardButton(text="⬅️ Cancel", callback_data="wizard:cancel"))
    return markup


def preset_times_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text=t, callback_data=f"time:{t}") for t in PRESET_TIMES]
    markup.add(*buttons, row_width=3)
    markup.add(
        InlineKeyboardButton(text="⌚ Enter custom time", callback_data="time:custom"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="wizard:back"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="wizard:cancel"),
    )
    return markup


def location_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="Skip", callback_data="location:skip"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="wizard:back"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="wizard:cancel"),
    )
    return markup


def note_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="Skip", callback_data="note:skip"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="wizard:back"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="wizard:cancel"),
    )
    return markup


def confirm_plan_keyboard(plan_id: Optional[int] = None) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    primary_label = "💾 Save" if plan_id is not None else "✅ Create"
    markup.add(
        InlineKeyboardButton(text=primary_label, callback_data="wizard:create"),
        InlineKeyboardButton(text="⬅️ Back", callback_data="wizard:back"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="wizard:cancel"),
    )
    return markup


def plan_owner_keyboard(plan_id: int, share_url: Optional[str] = None) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="✏️ Edit", callback_data=f"plan_edit:{plan_id}"),
        InlineKeyboardButton(text="🗑 Delete", callback_data=f"plan_delete:{plan_id}"),
    )
    if share_url:
        markup.add(InlineKeyboardButton(text="🔗 Share event", url=share_url))
    else:
        markup.add(InlineKeyboardButton(text="🔗 Share event", callback_data=f"plan_share:{plan_id}"))
    markup.add(InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back_home"))
    return markup


def plan_friend_keyboard(plan_id: int, joined: bool = False) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    if joined:
        markup.add(InlineKeyboardButton(text="✅ Joined", callback_data="noop:"))
    else:
        markup.add(InlineKeyboardButton(text="🙋 Join", callback_data=f"plan_join:{plan_id}"))
    markup.add(InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back_home"))
    return markup


def back_home_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back_home"))
    return markup


def share_link_keyboard(link: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Copy link", url=link))
    markup.add(InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back_home"))
    return markup


def plans_list_keyboard(plans: Iterable[int], action_prefix: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text=f"Open #{plan_id}", callback_data=f"{action_prefix}:{plan_id}") for plan_id in plans]
    if buttons:
        markup.add(*buttons, row_width=1)
    markup.add(InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back_home"))
    return markup
