from __future__ import annotations

from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SwitchInlineQueryChosenChat,
)

from app.callbacks.factories import (
    EventCallback,
    EventFlowCallback,
    ListCallback,
    MenuCallback,
    NavCallback,
)
from app.constants import HEBREW_MONTH_NAMES, Category, EventType, Gender
from app.core.hebcal import gematria
from app.i18n.translator import t
from app.keyboards.pagination import page_row

# S6 "more details" fields, in display order (SPEC.md 15/S6).
MORE_DETAILS_FIELDS = (
    "category",
    "relation",
    "phone",
    "nickname",
    "photo",
    "notes",
    "gender",
    "event_time",
)


def name_step_keyboard(lang: str) -> InlineKeyboardMarkup:
    cancel = InlineKeyboardButton(
        text=t("common.cancel", lang), callback_data=NavCallback(action="cancel").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[cancel]])


def date_step_keyboard(lang: str) -> InlineKeyboardMarkup:
    no_year = InlineKeyboardButton(
        text=t("add.date.no_year", lang), callback_data=EventFlowCallback(action="noyear").pack()
    )
    hebrew = InlineKeyboardButton(
        text=t("add.date.hebrew", lang), callback_data=EventFlowCallback(action="heb").pack()
    )
    cancel = InlineKeyboardButton(
        text=t("common.cancel", lang), callback_data=NavCallback(action="cancel").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[no_year], [hebrew], [cancel]])


def hebrew_month_keyboard() -> InlineKeyboardMarkup:
    """3-per-row grid of the 12 base Hebrew months (Adar's sub-choice is a separate step)."""
    buttons = [
        InlineKeyboardButton(
            text=HEBREW_MONTH_NAMES[i - 1],
            callback_data=EventFlowCallback(action="hm", value=str(i)).pack(),
        )
        for i in range(1, 13)
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    cancel = InlineKeyboardButton(
        text=t("common.cancel", "he"), callback_data=NavCallback(action="cancel").pack()
    )
    rows.append([cancel])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hebrew_adar_choice_keyboard() -> InlineKeyboardMarkup:
    adar_i = InlineKeyboardButton(
        text="אדר א׳", callback_data=EventFlowCallback(action="hm", value="12").pack()
    )
    adar_ii = InlineKeyboardButton(
        text="אדר ב׳", callback_data=EventFlowCallback(action="hm", value="13").pack()
    )
    plain = InlineKeyboardButton(
        text="סתם אדר", callback_data=EventFlowCallback(action="hm", value="12").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[adar_i, adar_ii], [plain]])


def hebrew_day_keyboard(month_length: int) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=gematria(day), callback_data=EventFlowCallback(action="hd", value=str(day)).pack()
        )
        for day in range(1, month_length + 1)
    ]
    rows = [buttons[i : i + 5] for i in range(0, len(buttons), 5)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hebrew_year_keyboard(lang: str) -> InlineKeyboardMarkup:
    no_year = InlineKeyboardButton(
        text=t("add.date.no_year", lang), callback_data=EventFlowCallback(action="noyear").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[no_year]])


def saved_keyboard(lang: str, event_id: int) -> InlineKeyboardMarkup:
    more = InlineKeyboardButton(
        text=t("add.more_details", lang), callback_data=EventFlowCallback(action="more").pack()
    )
    change_reminder = InlineKeyboardButton(
        text=t("add.change_reminder", lang),
        callback_data=EventCallback(action="rem", event_id=event_id).pack(),
    )
    add_another = InlineKeyboardButton(
        text=t("add.add_another", lang), callback_data=NavCallback(action="cancel").pack()
    )
    home = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[more, change_reminder], [add_another, home]])


def card_keyboard(
    lang: str, event_id: int, is_active: bool, share_text: str
) -> InlineKeyboardMarkup:
    def btn(action: str, key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=t(key, lang), callback_data=EventCallback(action=action, event_id=event_id).pack()
        )

    mute_key = "card.unmute" if not is_active else "card.mute"
    share_btn = InlineKeyboardButton(
        text=t("card.share", lang),
        switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
            query=share_text,
            allow_user_chats=True,
            allow_bot_chats=False,
            allow_group_chats=True,
            allow_channel_chats=False,
        ),
    )
    back = InlineKeyboardButton(
        text=t("card.back_to_list", lang), callback_data=MenuCallback(action="list").pack()
    )
    home = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [btn("e", "card.edit"), btn("gr", "card.greeting")],
            [btn("rem", "card.reminders_btn"), btn("mute", mute_key)],
            [share_btn, btn("d", "card.delete")],
            [back, home],
        ]
    )


def _field_display_value(lang: str, field: str, event: Any) -> str:
    model_field = "photo_file_id" if field == "photo" else field
    raw = getattr(event, model_field)
    if raw is None or raw == "":
        return t("common.unknown", lang) if field == "event_type" else "—"
    if field == "category":
        return t(f"category.{raw}", lang)
    if field == "gender":
        return t(f"gender.{raw}", lang)
    if field == "event_type":
        return t(f"event_type.{raw}", lang)
    if field == "photo":
        return t("common.saved", lang)
    return str(raw)


def more_details_keyboard(lang: str, event: Any) -> InlineKeyboardMarkup:
    """S6 field picker. Each button shows the field's current value."""

    def field_btn(field: str) -> InlineKeyboardButton:
        value = _field_display_value(lang, field, event)
        return InlineKeyboardButton(
            text=t(f"more.{field}", lang, value=value),
            callback_data=EventFlowCallback(action="field", value=field).pack(),
        )

    buttons = [field_btn(f) for f in MORE_DETAILS_FIELDS]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]

    type_btn = InlineKeyboardButton(
        text=t("more.event_type", lang, value=_field_display_value(lang, "event_type", event)),
        callback_data=EventFlowCallback(action="field", value="event_type").pack(),
    )
    done_btn = InlineKeyboardButton(
        text=t("more.done", lang), callback_data=EventFlowCallback(action="skip").pack()
    )
    rows.append([type_btn])
    rows.append([done_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def field_prompt_keyboard(lang: str, field: str, has_value: bool) -> InlineKeyboardMarkup:
    """`[דלג ←] [🗑 נקה] [← חזרה]` under a field's text-entry prompt."""
    skip = InlineKeyboardButton(
        text=t("common.skip", lang), callback_data=EventFlowCallback(action="skip").pack()
    )
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=EventFlowCallback(action="more").pack()
    )
    row = [skip]
    if has_value:
        clear = InlineKeyboardButton(
            text=t("field.clear", lang),
            callback_data=EventFlowCallback(action="clear", value=field).pack(),
        )
        row.append(clear)
    return InlineKeyboardMarkup(inline_keyboard=[row, [back]])


def category_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"category.{c.value}", lang),
            callback_data=EventFlowCallback(action="cat", value=c.value).pack(),
        )
        for c in Category
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=EventFlowCallback(action="more").pack()
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def gender_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"gender.{g.value}", lang),
            callback_data=EventFlowCallback(action="gender", value=g.value).pack(),
        )
        for g in Gender
    ]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=EventFlowCallback(action="more").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [back]])


def event_type_picker_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"event_type.{e.value}", lang),
            callback_data=EventFlowCallback(action="type", value=e.value).pack(),
        )
        for e in EventType
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=EventFlowCallback(action="more").pack()
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirm_keyboard(lang: str, event_id: int) -> InlineKeyboardMarkup:
    yes = InlineKeyboardButton(
        text=t("delete.confirm.yes", lang),
        callback_data=EventCallback(action="dy", event_id=event_id).pack(),
    )
    cancel = InlineKeyboardButton(
        text=t("common.cancel", lang), callback_data=NavCallback(action="cancel").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[yes, cancel]])


def delete_done_keyboard(lang: str, event_id: int) -> InlineKeyboardMarkup:
    undo = InlineKeyboardButton(
        text=t("delete.undo", lang),
        callback_data=EventCallback(action="undo", event_id=event_id).pack(),
    )
    back = InlineKeyboardButton(
        text=t("card.back_to_list", lang), callback_data=MenuCallback(action="list").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[[undo], [back]])


def list_keyboard(
    lang: str, row_labels: list[tuple[int, str]], page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """``row_labels`` is [(event_id, display_text), ...] for the current page (up to 8)."""
    event_rows = [
        [
            InlineKeyboardButton(
                text=label, callback_data=EventCallback(action="v", event_id=event_id).pack()
            )
        ]
        for event_id, label in row_labels
    ]

    sort_btn = InlineKeyboardButton(
        text=t("list.sort_btn", lang),
        callback_data=ListCallback(action="sort", value="menu").pack(),
    )
    filter_btn = InlineKeyboardButton(
        text=t("list.filter_btn", lang),
        callback_data=ListCallback(action="filt", value="menu").pack(),
    )
    search_btn = InlineKeyboardButton(
        text=t("list.search_btn", lang), callback_data=MenuCallback(action="srch").pack()
    )
    home_btn = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )

    controls_row = [sort_btn, filter_btn, search_btn]
    rows = [*event_rows, page_row(page, total_pages), controls_row, [home_btn]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


_SORT_OPTIONS = ("upcoming", "name", "age", "created")
_FILTER_OPTIONS = ("all", "muted")


def sort_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"list.sort_{opt}", lang),
            callback_data=ListCallback(action="fset", value=f"sort:{opt}").pack(),
        )
        for opt in _SORT_OPTIONS
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=MenuCallback(action="list").pack()
    )
    rows.append([back])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filter_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=t(f"list.filter_option_{opt}", lang),
            callback_data=ListCallback(action="fset", value=f"filt:{opt}").pack(),
        )
        for opt in _FILTER_OPTIONS
    ]
    back = InlineKeyboardButton(
        text=t("common.back", lang), callback_data=MenuCallback(action="list").pack()
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [back]])
