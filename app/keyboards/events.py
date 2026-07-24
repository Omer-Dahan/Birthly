from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import (
    EventCallback,
    EventFlowCallback,
    ListCallback,
    MenuCallback,
    NavCallback,
)
from app.constants import HEBREW_MONTH_NAMES
from app.core.hebcal import gematria
from app.i18n.translator import t
from app.keyboards.pagination import page_row


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
    back = InlineKeyboardButton(
        text=t("common.back", "he"), callback_data=NavCallback(action="back").pack()
    )
    rows.append([back])
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


def card_keyboard(lang: str, event_id: int, is_active: bool) -> InlineKeyboardMarkup:
    def btn(action: str, key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=t(key, lang), callback_data=EventCallback(action=action, event_id=event_id).pack()
        )

    mute_key = "card.unmute" if not is_active else "card.mute"
    back = InlineKeyboardButton(
        text=t("card.back_to_list", lang), callback_data=NavCallback(action="back").pack()
    )
    home = InlineKeyboardButton(
        text=t("common.home", lang), callback_data=NavCallback(action="home").pack()
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [btn("e", "card.edit"), btn("gr", "card.greeting")],
            [btn("rem", "card.reminders_btn"), btn("mute", mute_key)],
            [btn("sh", "card.share"), btn("d", "card.delete")],
            [back, home],
        ]
    )


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
        text=t("card.back_to_list", lang), callback_data=NavCallback(action="back").pack()
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
