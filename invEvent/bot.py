from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import telebot
from telebot import types

from . import db, keyboards, views
from .config import load_settings
from .services import plans, sharing, timeutil, users

logging.basicConfig(level=logging.INFO)

settings = load_settings()
db.init_db(settings.db_path)
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")


CALLBACK_COOLDOWN_SECONDS = 0.6
last_callback_at: Dict[int, float] = {}


@dataclass
class WizardState:
    stage: str
    data: Dict[str, Any] = field(default_factory=dict)
    plan_id: Optional[int] = None


user_states: Dict[int, WizardState] = {}


def throttle_callback(user_id: int) -> bool:
    now = time.monotonic()
    last = last_callback_at.get(user_id)
    if last is not None and (now - last) < CALLBACK_COOLDOWN_SECONDS:
        return True
    last_callback_at[user_id] = now
    return False


def send_home(chat_id: int) -> None:
    bot.send_message(
        chat_id,
        "What’s up for tomorrow?",
        reply_markup=keyboards.main_menu_keyboard(),
    )


def get_state(user_id: int) -> Optional[WizardState]:
    return user_states.get(user_id)


def set_state(user_id: int, state: Optional[WizardState]) -> None:
    if state is None:
        user_states.pop(user_id, None)
    else:
        user_states[user_id] = state


def start_wizard(user_id: int, chat_id: int, existing_plan: Optional[Dict[str, Any]] = None) -> None:
    data: Dict[str, Any] = {}
    plan_id = None
    if existing_plan:
        data = {
            "category": existing_plan["category"],
            "time_hm": existing_plan["time_hm"],
            "note": existing_plan.get("note"),
            "location_lat": existing_plan.get("location_lat"),
            "location_lon": existing_plan.get("location_lon"),
            "location_label": existing_plan.get("location_label"),
        }
        plan_id = existing_plan["id"]
    state = WizardState(stage="category", data=data, plan_id=plan_id)
    set_state(user_id, state)
    prompt_category(chat_id, data.get("category"))


def prompt_category(chat_id: int, current: Optional[str] = None) -> None:
    prefix = "Pick a category" if current is None else f"Pick a category (current: {current})"
    bot.send_message(chat_id, prefix, reply_markup=keyboards.categories_keyboard())


def prompt_time(chat_id: int, current: Optional[str] = None) -> None:
    prefix = "Choose a time" if current is None else f"Choose a time (current: {current})"
    bot.send_message(chat_id, prefix, reply_markup=keyboards.preset_times_keyboard())


def prompt_custom_time(chat_id: int) -> None:
    bot.send_message(chat_id, views.format_custom_time_prompt())


def prompt_location(chat_id: int, label: Optional[str]) -> None:
    base = views.format_location_prompt()
    if label:
        base = f"Current location: {label}\n\n" + base
    bot.send_message(chat_id, base, reply_markup=keyboards.location_keyboard())


def prompt_note(chat_id: int, note: Optional[str]) -> None:
    base = views.format_note_prompt()
    if note:
        base = f"Current note: {note}\n\n" + base
    bot.send_message(chat_id, base, reply_markup=keyboards.note_keyboard())


def prompt_confirm(chat_id: int, state: WizardState) -> None:
    text = views.format_confirm_message(
        state.data.get("category", ""),
        state.data.get("time_hm", ""),
        state.data.get("note"),
        state.data.get("location_label"),
    )
    bot.send_message(chat_id, text, reply_markup=keyboards.confirm_plan_keyboard(state.plan_id))


def send_plan_card(chat_id: int, plan: Dict[str, Any], viewer_id: int) -> None:
    if not timeutil.is_future(plan["time_utc"]):
        return
    time_hm = plan["time_hm"] or timeutil.display_time_from_utc_iso(plan["time_utc"])
    location_label = plan.get("location_label")
    if not location_label and plan.get("location_lat") and plan.get("location_lon"):
        location_label = "Location attached"
    text = views.format_plan_summary(plan["category"], time_hm, plan.get("note"), location_label)
    if viewer_id == plan["author_id"]:
        markup = keyboards.plan_owner_keyboard(plan["id"])
    else:
        joined = plans.has_joined_plan(viewer_id, plan["id"], plan["date_ymd"])
        markup = keyboards.plan_friend_keyboard(plan["id"], joined=joined)
    bot.send_message(chat_id, text, reply_markup=markup)
    if plan.get("location_lat") and plan.get("location_lon"):
        bot.send_location(chat_id, plan["location_lat"], plan["location_lon"])


def handle_start_deeplink(user_id: int, chat_id: int, payload: str) -> bool:
    if not payload.startswith("ev"):
        return False
    try:
        body = payload[2:]
        plan_part, token = body.split("_", maxsplit=1)
        plan_id = int(plan_part)
    except (ValueError, IndexError):
        return False

    redeemed = sharing.redeem_token(token, user_id)
    if not redeemed:
        bot.send_message(chat_id, views.format_token_invalid(), reply_markup=keyboards.back_home_keyboard())
        return True

    plan, sharer_id = redeemed
    users.add_friendship(user_id, sharer_id)
    send_plan_card(chat_id, plan, user_id)
    bot.send_message(chat_id, views.format_friend_join_confirmation(), reply_markup=keyboards.back_home_keyboard())
    return True


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message) -> None:
    user_id = users.ensure_user(message.from_user)
    parts = message.text.split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ""
    if payload:
        handled = handle_start_deeplink(user_id, message.chat.id, payload)
        if handled:
            return
    send_home(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: types.CallbackQuery) -> None:
    user_id = users.ensure_user(call.from_user)
    if throttle_callback(user_id):
        bot.answer_callback_query(call.id)
        return

    data = call.data or ""
    if data.startswith("noop"):
        bot.answer_callback_query(call.id)
        return

    if data.startswith("menu:"):
        handle_menu_callback(call, user_id)
    elif data.startswith("cat:"):
        handle_category_selected(call, user_id, data.split(":", 1)[1])
    elif data.startswith("time:"):
        handle_time_selected(call, user_id, data.split(":", 1)[1])
    elif data.startswith("location:" ):
        handle_location_callback(call, user_id, data.split(":", 1)[1])
    elif data.startswith("note:" ):
        handle_note_callback(call, user_id, data.split(":", 1)[1])
    elif data.startswith("wizard:"):
        handle_wizard_navigation(call, user_id, data.split(":", 1)[1])
    elif data.startswith("plan_edit:"):
        handle_plan_edit(call, user_id, int(data.split(":", 1)[1]))
    elif data.startswith("plan_delete:"):
        handle_plan_delete(call, user_id, int(data.split(":", 1)[1]))
    elif data.startswith("plan_share:"):
        handle_plan_share(call, user_id, int(data.split(":", 1)[1]))
    elif data.startswith("plan_join:"):
        handle_plan_join(call, user_id, int(data.split(":", 1)[1]))
    elif data.startswith("nav:" ):
        handle_nav(call, user_id, data.split(":", 1)[1])
    else:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)


def handle_menu_callback(call: types.CallbackQuery, user_id: int) -> None:
    action = call.data.split(":", 1)[1]
    chat_id = call.message.chat.id
    if action == "new_plan":
        start_wizard(user_id, chat_id)
    elif action == "friends":
        show_friend_plans(chat_id, user_id)
    elif action == "mine":
        show_my_plans(chat_id, user_id)
    elif action == "settings":
        bot.send_message(chat_id, views.format_settings_placeholder(), reply_markup=keyboards.back_home_keyboard())


def show_my_plans(chat_id: int, user_id: int) -> None:
    user_plans = plans.list_user_plans(user_id)
    if not user_plans:
        bot.send_message(chat_id, views.format_no_plans_message(owner=True), reply_markup=keyboards.back_home_keyboard())
        return
    bot.send_message(chat_id, "📋 Your plans for tomorrow", reply_markup=keyboards.back_home_keyboard())
    for plan_item in user_plans:
        send_plan_card(chat_id, plan_item, user_id)


def show_friend_plans(chat_id: int, user_id: int) -> None:
    friend_ids = users.list_friend_ids(user_id)
    friend_plans = plans.list_friend_plans(user_id, friend_ids)
    if not friend_plans:
        bot.send_message(chat_id, views.format_no_plans_message(owner=False), reply_markup=keyboards.back_home_keyboard())
        return
    bot.send_message(chat_id, views.format_friend_list_header(), reply_markup=keyboards.back_home_keyboard())
    for plan_item in friend_plans:
        send_plan_card(chat_id, plan_item, user_id)


def handle_category_selected(call: types.CallbackQuery, user_id: int, category: str) -> None:
    state = get_state(user_id)
    if not state or state.stage != "category":
        return
    state.data["category"] = category
    state.stage = "time"
    prompt_time(call.message.chat.id)


def handle_time_selected(call: types.CallbackQuery, user_id: int, time_value: str) -> None:
    state = get_state(user_id)
    if not state or state.stage not in {"time", "custom_time_input"}:
        return
    if time_value == "custom":
        state.stage = "custom_time_input"
        prompt_custom_time(call.message.chat.id)
        return
    state.data["time_hm"] = time_value
    state.stage = "location"
    prompt_location(call.message.chat.id, state.data.get("location_label"))


def handle_location_callback(call: types.CallbackQuery, user_id: int, action: str) -> None:
    state = get_state(user_id)
    if not state or state.stage != "location":
        return
    if action == "skip":
        state.data["location_lat"] = None
        state.data["location_lon"] = None
        state.data["location_label"] = None
        state.stage = "note"
        prompt_note(call.message.chat.id, state.data.get("note"))
    elif action == "back":
        state.stage = "time"
        prompt_time(call.message.chat.id, state.data.get("time_hm"))
    elif action == "cancel":
        cancel_wizard(call.message.chat.id, user_id)


def handle_note_callback(call: types.CallbackQuery, user_id: int, action: str) -> None:
    state = get_state(user_id)
    if not state or state.stage != "note":
        return
    if action == "skip":
        state.data["note"] = None
        state.stage = "confirm"
        prompt_confirm(call.message.chat.id, state)
    elif action == "back":
        state.stage = "location"
        prompt_location(call.message.chat.id, state.data.get("location_label"))
    elif action == "cancel":
        cancel_wizard(call.message.chat.id, user_id)


def handle_wizard_navigation(call: types.CallbackQuery, user_id: int, action: str) -> None:
    state = get_state(user_id)
    if not state:
        return
    chat_id = call.message.chat.id
    if action == "cancel":
        cancel_wizard(chat_id, user_id)
    elif action == "back":
        wizard_go_back(chat_id, user_id)
    elif action == "create":
        finalize_wizard(chat_id, user_id)


def cancel_wizard(chat_id: int, user_id: int) -> None:
    set_state(user_id, None)
    bot.send_message(chat_id, "Cancelled.")
    send_home(chat_id)


def wizard_go_back(chat_id: int, user_id: int) -> None:
    state = get_state(user_id)
    if not state:
        send_home(chat_id)
        return
    if state.stage == "category":
        set_state(user_id, None)
        send_home(chat_id)
    elif state.stage == "time":
        state.stage = "category"
        prompt_category(chat_id, state.data.get("category"))
    elif state.stage == "custom_time_input":
        state.stage = "time"
        prompt_time(chat_id, state.data.get("time_hm"))
    elif state.stage == "location":
        state.stage = "time"
        prompt_time(chat_id, state.data.get("time_hm"))
    elif state.stage == "note":
        state.stage = "location"
        prompt_location(chat_id, state.data.get("location_label"))
    elif state.stage == "confirm":
        state.stage = "note"
        prompt_note(chat_id, state.data.get("note"))


def finalize_wizard(chat_id: int, user_id: int) -> None:
    state = get_state(user_id)
    if not state:
        return
    required = (state.data.get("category"), state.data.get("time_hm"))
    if not all(required):
        bot.send_message(chat_id, "Please complete all steps.")
        return
    if state.plan_id:
        updated = plans.update_plan(
            state.plan_id,
            user_id,
            state.data["category"],
            state.data["time_hm"],
            state.data.get("note"),
            state.data.get("location_lat"),
            state.data.get("location_lon"),
            state.data.get("location_label"),
        )
        if updated:
            bot.send_message(chat_id, views.format_plan_updated())
            plan = plans.get_plan(state.plan_id)
            if plan:
                send_plan_card(chat_id, plan, user_id)
    else:
        plan_id = plans.create_plan(
            user_id,
            state.data["category"],
            state.data["time_hm"],
            state.data.get("note"),
            state.data.get("location_lat"),
            state.data.get("location_lon"),
            state.data.get("location_label"),
            state.data.get("base_plan_id"),
        )
        bot.send_message(chat_id, views.format_plan_created())
        plan = plans.get_plan(plan_id)
        if plan:
            send_plan_card(chat_id, plan, user_id)
    set_state(user_id, None)


def handle_plan_edit(call: types.CallbackQuery, user_id: int, plan_id: int) -> None:
    plan = plans.get_plan(plan_id)
    if not plan or plan["author_id"] != user_id:
        bot.send_message(call.message.chat.id, views.format_plan_not_found())
        return
    start_wizard(user_id, call.message.chat.id, existing_plan=plan)


def handle_plan_delete(call: types.CallbackQuery, user_id: int, plan_id: int) -> None:
    if plans.delete_plan(plan_id, user_id):
        bot.send_message(call.message.chat.id, views.format_plan_deleted(), reply_markup=keyboards.back_home_keyboard())
    else:
        bot.send_message(call.message.chat.id, views.format_plan_not_found(), reply_markup=keyboards.back_home_keyboard())


def handle_plan_share(call: types.CallbackQuery, user_id: int, plan_id: int) -> None:
    plan = plans.get_plan(plan_id)
    if not plan or plan["author_id"] != user_id:
        bot.send_message(call.message.chat.id, views.format_plan_not_found())
        return
    token = sharing.create_share_token(user_id, plan_id, settings.share_token_ttl_hours)
    link = f"https://t.me/{settings.bot_username}?start=ev{plan_id}_{token}"
    bot.send_message(call.message.chat.id, views.format_share_token_created(), reply_markup=keyboards.share_link_keyboard(link))


def handle_plan_join(call: types.CallbackQuery, user_id: int, plan_id: int) -> None:
    plan = plans.get_plan(plan_id)
    if not plan:
        bot.send_message(call.message.chat.id, views.format_plan_not_found())
        return
    if plan["author_id"] == user_id:
        bot.send_message(call.message.chat.id, views.format_plan_joined_already())
        return
    if not users.are_friends(user_id, plan["author_id"]):
        bot.send_message(call.message.chat.id, "You need to be friends to join this plan.")
        return
    if not timeutil.is_future(plan["time_utc"]):
        bot.send_message(call.message.chat.id, views.format_plan_not_found())
        return
    if plans.has_joined_plan(user_id, plan_id, plan["date_ymd"]):
        bot.send_message(call.message.chat.id, views.format_plan_joined_already())
        return
    new_plan_id = plans.create_plan(
        user_id,
        plan["category"],
        plan["time_hm"],
        plan.get("note"),
        plan.get("location_lat"),
        plan.get("location_lon"),
        plan.get("location_label"),
        base_plan_id=plan_id,
        date_ymd=plan["date_ymd"],
    )
    bot.send_message(call.message.chat.id, "Added to your plans!")
    joined_plan = plans.get_plan(new_plan_id)
    if joined_plan:
        send_plan_card(call.message.chat.id, joined_plan, user_id)


def handle_nav(call: types.CallbackQuery, user_id: int, action: str) -> None:
    if action == "back_home":
        set_state(user_id, None)
        send_home(call.message.chat.id)


@bot.message_handler(content_types=["location"])
def handle_location_message(message: types.Message) -> None:
    user_id = users.ensure_user(message.from_user)
    state = get_state(user_id)
    if not state or state.stage != "location":
        return
    location = message.location
    state.data["location_lat"] = location.latitude
    state.data["location_lon"] = location.longitude
    state.data["location_label"] = "Pinned location"
    state.stage = "note"
    prompt_note(message.chat.id, state.data.get("note"))


@bot.message_handler(content_types=["text"])
def handle_text_message(message: types.Message) -> None:
    user_id = users.ensure_user(message.from_user)
    state = get_state(user_id)
    if state is None:
        return
    if state.stage == "custom_time_input":
        try:
            local_dt = timeutil.parse_time_hm(message.text.strip())
        except ValueError:
            bot.send_message(message.chat.id, "Please send time as HH:MM (24h).")
            return
        state.data["time_hm"] = local_dt.strftime("%H:%M")
        state.stage = "location"
        prompt_location(message.chat.id, state.data.get("location_label"))
    elif state.stage == "location":
        label = message.text.strip()
        if not label:
            bot.send_message(message.chat.id, "Please send a location name or choose skip.")
            return
        state.data["location_label"] = label[:120]
        state.data["location_lat"] = None
        state.data["location_lon"] = None
        state.stage = "note"
        prompt_note(message.chat.id, state.data.get("note"))
    elif state.stage == "note":
        note = message.text.strip()
        if len(note) > 120:
            bot.send_message(message.chat.id, "Note too long (max 120 chars).")
            return
        state.data["note"] = note if note else None
        state.stage = "confirm"
        prompt_confirm(message.chat.id, state)


def main() -> None:
    bot.infinity_polling(timeout=20, long_polling_timeout=20)


if __name__ == "__main__":
    main()
