"""Greeting / template handler. Implements S14. See SPEC.md chapters 15 and 22.

Callback flow:
  ev:gr:<id>            → show tone picker (S14 style screen)
  tpl:style:<event_id>  → same (back from result/list/AI screens)
  tpl:pick:<tone>:<event_id>[:<exclude_id>] → render a seeded/personal greeting
  tpl:ai:<event_id>     → build a copy-paste prompt for the user's own AI
  tpl:list:<event_id>   → list personal templates ("✏️ שלי")
  tpl:use:<id>:<event_id> → render a specific personal template
  tpl:new:<event_id>    → (TemplateFlow.body, via new_tone) create a personal template
  tpl:del:<id>:<event_id> → delete a personal template
"""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.factories import EventCallback, TemplateCallback
from app.core.formatting import format_name
from app.core.text import esc
from app.db.models import User
from app.db.repositories.templates import TemplateRepository
from app.i18n.translator import t
from app.keyboards.templates import (
    ai_prompt_keyboard,
    greeting_result_keyboard,
    greeting_style_keyboard,
    personal_templates_keyboard,
    template_new_keyboard,
)
from app.services.event_service import get_owned_event
from app.services.exceptions import LimitError, NotFoundError
from app.services.template_service import (
    build_ai_prompt,
    create_user_template,
    delete_user_template,
    pick_template,
    render_template,
)
from app.states.forms import TemplateFlow
from app.utils.telegram import edit_or_ignore

router = Router(name="templates")

_VALID_TONES = {"warm", "funny", "formal", "short"}


# ── S14: show tone picker ──────────────────────────────────────────────────


@router.callback_query(EventCallback.filter(F.action == "gr"))
async def cb_greeting_style(
    callback: CallbackQuery, callback_data: EventCallback, session: Any, user: User
) -> None:
    """ev:gr:<id> → display the tone-picker keyboard."""
    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    # memorial events have no greetings (SPEC §22)
    if event.event_type == "memorial":
        await callback.answer(t("greeting.no_memorial", user.language), show_alert=True)
        return

    name = esc(format_name(event.first_name, event.last_name))
    text = t("greeting.style.title", user.language, name=name)
    keyboard = greeting_style_keyboard(user.language, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


@router.callback_query(TemplateCallback.filter(F.action == "style"))
async def cb_back_to_style(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    """tpl:style:<event_id> — back from result to tone picker."""
    if callback_data.event_id is None:
        await callback.answer()
        return
    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    name = esc(format_name(event.first_name, event.last_name))
    text = t("greeting.style.title", user.language, name=name)
    keyboard = greeting_style_keyboard(user.language, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


# ── S14: render a greeting ─────────────────────────────────────────────────


@router.callback_query(TemplateCallback.filter(F.action == "pick"))
async def cb_greeting_pick(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    """tpl:pick:<tone>:<event_id>[:<exclude_id>] — exclude_id avoids repeating
    the template that was just shown when the user taps "🔄 עוד אחת"."""
    if callback_data.event_id is None or callback_data.value is None:
        await callback.answer()
        return

    tone = callback_data.value
    exclude_id = callback_data.exclude_id

    if tone not in _VALID_TONES:
        await callback.answer(t("error.generic", user.language), show_alert=True)
        return

    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    tpl = await pick_template(session, user, event, tone, exclude_id=exclude_id)
    if tpl is None:
        await callback.answer(t("greeting.no_templates", user.language), show_alert=True)
        return

    greeting_text = render_template(tpl, event, user)
    name = esc(format_name(event.first_name, event.last_name))

    body = (
        f"💌 {t('greeting.result.title', user.language, name=name)}\n\n"
        f"<code>{esc(greeting_text)}</code>\n\n"
        f"<i>{t('greeting.result.hint', user.language)}</i>"
    )
    keyboard = greeting_result_keyboard(
        user.language, callback_data.event_id, tone, tpl.id, greeting_text
    )
    await edit_or_ignore(callback, body, keyboard)
    await callback.answer()


# ── S14: AI hand-off ────────────────────────────────────────────────────────


@router.callback_query(TemplateCallback.filter(F.action == "ai"))
async def cb_greeting_ai(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    """🤖 AI — build a copy-paste prompt instead of picking a seeded template.

    The bot never calls an AI itself; it only prepares text the user pastes
    into whatever assistant they already use.
    """
    if callback_data.event_id is None:
        await callback.answer()
        return
    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    prompt = build_ai_prompt(event, user, "warm")
    text = (
        f"🤖 {t('greeting.ai.title', user.language)}\n\n"
        f"<code>{esc(prompt)}</code>\n\n"
        f"<i>{t('greeting.ai.hint', user.language)}</i>"
    )
    keyboard = ai_prompt_keyboard(user.language, callback_data.event_id)
    await edit_or_ignore(callback, text, keyboard)
    await callback.answer()


# ── S14: personal templates list ("✏️ שלי") ─────────────────────────────────


async def _render_personal_list(
    callback: CallbackQuery, session: Any, user: User, event_id: int
) -> None:
    repo = TemplateRepository(session, user.id)
    templates = await repo.list_user_templates()
    rows = [(tpl.id, tpl.body[:40] + ("…" if len(tpl.body) > 40 else "")) for tpl in templates]

    if not rows:
        text = t("greeting.new.no_personal", user.language)
    else:
        text = t("greeting.new.personal_title", user.language)

    keyboard = personal_templates_keyboard(user.language, event_id, rows)
    await edit_or_ignore(callback, text, keyboard)


@router.callback_query(TemplateCallback.filter(F.action == "list"))
async def cb_list_personal(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    if callback_data.event_id is None:
        await callback.answer()
        return
    try:
        await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await _render_personal_list(callback, session, user, callback_data.event_id)
    await callback.answer()


@router.callback_query(TemplateCallback.filter(F.action == "use"))
async def cb_use_personal_template(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    """Render a specific personal template picked from the "✏️ שלי" list."""
    if callback_data.event_id is None or callback_data.value is None:
        await callback.answer()
        return

    repo = TemplateRepository(session, user.id)
    tpl = await repo.get_owned(int(callback_data.value))
    if tpl is None:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    try:
        event = await get_owned_event(session, user, callback_data.event_id)
    except NotFoundError:
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return

    greeting_text = render_template(tpl, event, user)
    name = esc(format_name(event.first_name, event.last_name))
    body = (
        f"💌 {t('greeting.result.title', user.language, name=name)}\n\n"
        f"<code>{esc(greeting_text)}</code>\n\n"
        f"<i>{t('greeting.result.hint', user.language)}</i>"
    )
    keyboard = greeting_result_keyboard(
        user.language, callback_data.event_id, tpl.tone, tpl.id, greeting_text
    )
    await edit_or_ignore(callback, body, keyboard)
    await callback.answer()


# ── personal template creation ─────────────────────────────────────────────


@router.callback_query(TemplateCallback.filter(F.action == "new"))
async def cb_template_new(
    callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext, user: User
) -> None:
    """➕ צור חדשה on the personal-templates list — pick a tone first."""
    if callback_data.event_id is None:
        await callback.answer()
        return
    await state.update_data(new_event_id=callback_data.event_id)
    await edit_or_ignore(
        callback, t("greeting.new.pick_tone", user.language), template_new_keyboard(user.language)
    )
    await callback.answer()


@router.callback_query(TemplateCallback.filter(F.action == "new_tone"))
async def cb_template_new_tone(
    callback: CallbackQuery, callback_data: TemplateCallback, state: FSMContext, user: User
) -> None:
    """User picked a tone for their new personal template."""
    if callback_data.value not in _VALID_TONES:
        await callback.answer()
        return
    await state.set_state(TemplateFlow.body)
    await state.update_data(new_tone=callback_data.value)
    await edit_or_ignore(callback, t("greeting.new.body_prompt", user.language))
    await callback.answer()


@router.message(TemplateFlow.body)
async def msg_template_body(message: Message, state: FSMContext, session: Any, user: User) -> None:
    """Receive the body text for a new personal template."""
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("greeting.new.body_empty", user.language))
        return

    data = await state.get_data()
    tone = data.get("new_tone", "warm")
    event_id = data.get("new_event_id")
    try:
        await create_user_template(
            session, user, event_type="birthday", tone=tone, gender=None, body=text
        )
    except LimitError:
        await state.clear()
        await message.answer(t("error.limit_reached", user.language, max=20))
        return

    await state.clear()
    text_out = t("greeting.new.saved", user.language)
    if event_id is not None:
        repo = TemplateRepository(session, user.id)
        templates = await repo.list_user_templates()
        rows = [(tpl.id, tpl.body[:40] + ("…" if len(tpl.body) > 40 else "")) for tpl in templates]
        await message.answer(
            text_out, reply_markup=personal_templates_keyboard(user.language, event_id, rows)
        )
    else:
        await message.answer(text_out)


# ── personal template deletion ─────────────────────────────────────────────


@router.callback_query(TemplateCallback.filter(F.action == "del"))
async def cb_template_delete(
    callback: CallbackQuery, callback_data: TemplateCallback, session: Any, user: User
) -> None:
    if callback_data.value is None:
        await callback.answer()
        return
    try:
        tpl_id = int(callback_data.value)
        await delete_user_template(session, user, tpl_id)
    except (ValueError, NotFoundError):
        await callback.answer(t("error.not_found", user.language), show_alert=True)
        return
    await callback.answer(t("common.deleted", user.language))

    if callback_data.event_id is not None:
        await _render_personal_list(callback, session, user, callback_data.event_id)
