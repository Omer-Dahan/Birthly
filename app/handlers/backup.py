"""Backup / export / import handler. Implements S15. See SPEC.md chapter 23.

Callback flow:
  bk:home                    → main backup screen
  bk:exp:<json|csv|xlsx>     → export and send as document
  bk:imp                     → ask user to send a file (ImportFlow.waiting_file)
  bk:imp_do:<add|replace|replace_confirmed> → execute import
  bk:auto:<0|1>              → toggle auto-backup

FSM:
  ImportFlow.waiting_file    → user sends a .json document
  ImportFlow.confirm         → user picks add / replace mode
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Document,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.callbacks.factories import BackupCallback, NavCallback
from app.config import settings
from app.db.models import User
from app.i18n.translator import t
from app.keyboards.backup import (
    backup_home_keyboard,
    import_mode_keyboard,
    import_replace_confirm_keyboard,
)
from app.services.backup_service import (
    do_import,
    export_csv,
    export_json,
    export_xlsx,
    parse_import_json,
)
from app.states.forms import ImportFlow
from app.utils.telegram import edit_or_ignore

logger = logging.getLogger(__name__)
router = Router(name="backup")

_MAX_IMPORT_BYTES = 5 * 1024 * 1024  # 5 MB


# ── helpers ────────────────────────────────────────────────────────────────


def _backup_home_text(user: User) -> str:

    lang = user.language
    return t("backup.home.title", lang)


async def _send_backup_home(callback: CallbackQuery, user: User, session: Any) -> None:
    from app.db.repositories.events import EventRepository

    repo = EventRepository(session, user.id)
    count = await repo.count_not_deleted()
    lang = user.language

    text = (
        f"💾 <b>{t('backup.home.title', lang)}</b>\n\n"
        f"📦 {count} {t('backup.home.records', lang)}\n"
        f"🕐 {t('backup.home.auto_last', lang, time=settings.auto_backup_time)}"
    )
    keyboard = backup_home_keyboard(lang, auto_enabled=settings.auto_backup_enabled)
    await edit_or_ignore(callback, text, keyboard)


# ── S15 main screen ────────────────────────────────────────────────────────


@router.callback_query(BackupCallback.filter(F.action == "home"))
async def cb_backup_home(callback: CallbackQuery, session: Any, user: User) -> None:
    await _send_backup_home(callback, user, session)
    await callback.answer()


# ── export ─────────────────────────────────────────────────────────────────


@router.callback_query(BackupCallback.filter(F.action == "exp"))
async def cb_export(
    callback: CallbackQuery, callback_data: BackupCallback, session: Any, user: User
) -> None:
    fmt = callback_data.value
    if fmt not in ("json", "csv", "xlsx"):
        await callback.answer()
        return

    await callback.answer(t("backup.exporting", user.language))

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    filename = f"birthly_{user.id}_{timestamp}.{fmt}"

    try:
        if fmt == "json":
            data = await export_json(session, user)
        elif fmt == "csv":
            data = await export_csv(session, user)
        else:
            data = await export_xlsx(session, user)
    except Exception:
        logger.exception("export_failed", extra={"user_id": user.id, "format": fmt})
        if isinstance(callback.message, Message):
            await callback.message.answer(t("error.generic", user.language))
        return

    doc = BufferedInputFile(data, filename=filename)
    caption = t("backup.export_caption", user.language, fmt=fmt.upper())
    if isinstance(callback.message, Message):
        await callback.message.answer_document(doc, caption=caption)
        if fmt == "json":
            await callback.message.answer(t("backup.export_no_photos", user.language))


# ── import ─────────────────────────────────────────────────────────────────


@router.callback_query(BackupCallback.filter(F.action == "imp"))
async def cb_import_start(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    """Ask the user to send a JSON file."""
    await state.set_state(ImportFlow.waiting_file)
    text = t("backup.import_send_file", user.language)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("common.cancel", user.language),
                    callback_data=NavCallback(action="cancel").pack(),
                )
            ]
        ]
    )
    await edit_or_ignore(callback, text, cancel_kb)
    await callback.answer()


@router.message(ImportFlow.waiting_file, F.document)
async def msg_import_file(message: Message, state: FSMContext, session: Any, user: User) -> None:
    """Receive the document, parse it, show a preview."""
    doc: Document | None = message.document
    if doc is None:
        await message.answer(t("backup.import_no_file", user.language))
        return

    if doc.mime_type not in ("application/json", "text/plain") and not (
        doc.file_name or ""
    ).endswith(".json"):
        await message.answer(t("backup.import_wrong_format", user.language))
        return

    if doc.file_size and doc.file_size > _MAX_IMPORT_BYTES:
        await message.answer(t("backup.import_too_large", user.language, max_mb=5))
        return

    bot = message.bot
    assert bot is not None
    file = await bot.get_file(doc.file_id)
    assert file.file_path is not None
    raw = await bot.download_file(file.file_path)
    data = raw.read() if raw else b""

    try:
        payload, result = await parse_import_json(data)
    except (ValueError, Exception) as exc:
        await message.answer(t("backup.import_parse_error", user.language, error=str(exc)))
        await state.clear()
        return

    await state.set_state(ImportFlow.confirm)
    await state.update_data(import_payload=payload)

    preview_text = (
        f"{t('backup.import_preview.title', user.language)}\n\n"
        f"📦 {t('backup.import_preview.records', user.language, count=result.total_parsed)}\n"
    )
    if result.errors:
        preview_text += (
            f"⚠️ {t('backup.import_preview.errors', user.language, count=len(result.errors))}\n"
        )

    await message.answer(preview_text, reply_markup=import_mode_keyboard(user.language))


@router.callback_query(BackupCallback.filter(F.action == "imp_do"))
async def cb_import_do(
    callback: CallbackQuery,
    callback_data: BackupCallback,
    state: FSMContext,
    session: Any,
    user: User,
) -> None:
    mode = callback_data.value
    if mode not in ("add", "replace", "replace_confirmed"):
        await callback.answer()
        return

    if mode == "replace":
        # Require a second confirmation for destructive mode
        text = t("backup.import_replace_warning", user.language)
        await edit_or_ignore(callback, text, import_replace_confirm_keyboard(user.language))
        await callback.answer()
        return

    data = await state.get_data()
    payload = data.get("import_payload")
    if not payload:
        await callback.answer(t("error.generic", user.language), show_alert=True)
        await state.clear()
        return

    await callback.answer(t("backup.importing", user.language))

    actual_mode = "replace" if mode == "replace_confirmed" else "add"
    try:
        result = await do_import(session, user, payload, mode=actual_mode)
    except Exception:
        logger.exception("import_failed", extra={"user_id": user.id})
        if isinstance(callback.message, Message):
            await callback.message.answer(t("error.generic", user.language))
        await state.clear()
        return

    await state.clear()

    summary = (
        f"✅ {t('backup.import_done.title', user.language)}\n\n"
        f"📦 {t('backup.import_done.imported', user.language, count=result.imported)}\n"
        f"🔁 {t('backup.import_done.duplicates', user.language, count=result.duplicates)}\n"
    )
    if result.errors:
        error_rows = ", ".join(result.errors[:5])
        errors_line = t(
            "backup.import_done.errors",
            user.language,
            count=len(result.errors),
            rows=error_rows,
        )
        summary += f"⚠️ {errors_line}\n"

    if isinstance(callback.message, Message):
        await callback.message.answer(summary)


# ── auto-backup toggle ─────────────────────────────────────────────────────


@router.callback_query(BackupCallback.filter(F.action == "auto"))
async def cb_auto_backup_toggle(
    callback: CallbackQuery, callback_data: BackupCallback, user: User, session: Any
) -> None:
    # Settings-level toggle (note: settings is a global object; for per-user
    # toggling we'd update user.daily_digest_enabled — here we update the
    # user-level auto-backup preference if it were in the model; since it is
    # not, we just acknowledge and show the current state).
    # Per SPEC the auto-backup is a global server setting, not per-user.
    # We reflect the toggle in the UI only.
    enabled = callback_data.value == "1"
    await callback.answer(
        t(
            "backup.auto_toggled",
            user.language,
            state=t("common.yes" if enabled else "common.no", user.language),
        )
    )
    await _send_backup_home(callback, user, session)
