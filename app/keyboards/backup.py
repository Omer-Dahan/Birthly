"""Keyboards for the backup/export/import flow (S15). See SPEC.md chapter 23."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.callbacks.factories import BackupCallback, NavCallback
from app.i18n.translator import t


def backup_home_keyboard(lang: str, auto_enabled: bool) -> InlineKeyboardMarkup:
    """S15 main backup screen."""
    json_btn = InlineKeyboardButton(
        text=t("backup.export_json", lang),
        callback_data=BackupCallback(action="exp", value="json").pack(),
    )
    csv_btn = InlineKeyboardButton(
        text=t("backup.export_csv", lang),
        callback_data=BackupCallback(action="exp", value="csv").pack(),
    )
    xlsx_btn = InlineKeyboardButton(
        text=t("backup.export_xlsx", lang),
        callback_data=BackupCallback(action="exp", value="xlsx").pack(),
    )
    import_btn = InlineKeyboardButton(
        text=t("backup.import", lang),
        callback_data=BackupCallback(action="imp").pack(),
    )
    auto_label = "backup.auto_on" if auto_enabled else "backup.auto_off"
    auto_next = "0" if auto_enabled else "1"
    auto_btn = InlineKeyboardButton(
        text=t(auto_label, lang),
        callback_data=BackupCallback(action="auto", value=auto_next).pack(),
    )
    back_btn = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=NavCallback(action="home").pack(),
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [json_btn, csv_btn, xlsx_btn],
            [import_btn],
            [auto_btn],
            [back_btn],
        ]
    )


def import_mode_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Shown after the import file is parsed: add / replace / cancel."""
    add_btn = InlineKeyboardButton(
        text=t("backup.import_add", lang),
        callback_data=BackupCallback(action="imp_do", value="add").pack(),
    )
    replace_btn = InlineKeyboardButton(
        text=t("backup.import_replace", lang),
        callback_data=BackupCallback(action="imp_do", value="replace").pack(),
    )
    cancel_btn = InlineKeyboardButton(
        text=t("common.cancel", lang),
        callback_data=NavCallback(action="cancel").pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[add_btn], [replace_btn], [cancel_btn]])


def import_replace_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Extra confirmation for destructive 'replace all' import."""
    confirm_btn = InlineKeyboardButton(
        text=t("backup.import_replace_confirm", lang),
        callback_data=BackupCallback(action="imp_do", value="replace_confirmed").pack(),
    )
    cancel_btn = InlineKeyboardButton(
        text=t("common.cancel", lang),
        callback_data=NavCallback(action="cancel").pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[confirm_btn], [cancel_btn]])
