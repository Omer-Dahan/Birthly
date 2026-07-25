from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import NavCallback, ReminderCallback
from app.constants import REMINDER_OFFSET_CHOICES
from app.db.models import ReminderRule
from app.i18n.translator import t

_TIME_CHOICES = ("08:00", "09:00", "10:00", "12:00", "18:00", "20:00")


def rules_list_keyboard(
    lang: str, rules: list[ReminderRule], event_id: int | None
) -> InlineKeyboardMarkup:
    """S11 reminders screen: one toggle button per rule + add/mute-all/home."""
    rows = [
        [
            InlineKeyboardButton(
                text=_rule_label(rule, lang),
                callback_data=ReminderCallback(
                    action="menu", value=str(rule.id), event_id=event_id
                ).pack(),
            )
        ]
        for rule in rules
    ]
    add_btn = InlineKeyboardButton(
        text=t("rem.add", lang),
        callback_data=ReminderCallback(action="add", event_id=event_id).pack(),
    )
    home_btn = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    rows.append([add_btn])
    rows.append([home_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _rule_label(rule: ReminderRule, lang: str) -> str:
    label = t(f"rem.offset.{rule.offset_days}", lang) if rule.offset_days is not None else "?"
    time_str = rule.send_time or "—"
    key = "rem.rule_on" if rule.enabled else "rem.rule_off"
    return t(key, lang, label=label, time=time_str)


def add_rule_keyboard(lang: str, event_id: int | None) -> InlineKeyboardMarkup:
    def btn(offset: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=t(f"rem.offset.{offset}", lang),
            callback_data=ReminderCallback(
                action="off", value=str(offset), event_id=event_id
            ).pack(),
        )

    buttons = [btn(o) for o in REMINDER_OFFSET_CHOICES]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    back = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=ReminderCallback(action="back", event_id=event_id).pack(),
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rule_menu_keyboard(lang: str, rule_id: int, event_id: int | None) -> InlineKeyboardMarkup:
    toggle = InlineKeyboardButton(
        text=t("rem.toggle", lang),
        callback_data=ReminderCallback(action="tog", value=str(rule_id), event_id=event_id).pack(),
    )
    change_time = InlineKeyboardButton(
        text=t("rem.change_time", lang),
        callback_data=ReminderCallback(
            action="time_menu", value=str(rule_id), event_id=event_id
        ).pack(),
    )
    delete = InlineKeyboardButton(
        text=t("rem.delete_rule", lang),
        callback_data=ReminderCallback(action="del", value=str(rule_id), event_id=event_id).pack(),
    )
    back = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=ReminderCallback(action="back", event_id=event_id).pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[toggle], [change_time], [delete], [back]])


def time_choice_keyboard(lang: str, rule_id: int, event_id: int | None) -> InlineKeyboardMarkup:
    """``value`` packs ``<HH-MM>:<rule_id>`` — SPEC.md's ``rem:time:<HH-MM>`` schema
    extended with the rule id, since ``ReminderCallback`` has no third slot."""

    def btn(time_str: str) -> InlineKeyboardButton:
        packed_time = time_str.replace(":", "-")
        return InlineKeyboardButton(
            text=time_str,
            callback_data=ReminderCallback(
                action="time", value=f"{packed_time}:{rule_id}", event_id=event_id
            ).pack(),
        )

    buttons = [btn(tm) for tm in _TIME_CHOICES]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    back = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=ReminderCallback(action="menu", value=str(rule_id), event_id=event_id).pack(),
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)
