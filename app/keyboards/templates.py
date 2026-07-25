"""Keyboards for the greeting/templates flow (S14). See SPEC.md chapter 15/S14."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat

from app.callbacks.factories import EventCallback, NavCallback, TemplateCallback
from app.i18n.translator import t

_TONES = ("warm", "funny", "formal", "short")
_TONE_ICONS = {"warm": "💖", "funny": "😄", "formal": "👔", "short": "⚡"}


def greeting_style_keyboard(lang: str, event_id: int) -> InlineKeyboardMarkup:
    """S14 — pick a greeting tone (warm / funny / formal / short), or hand off to
    the user's own AI assistant, or manage personal templates."""
    buttons = [
        InlineKeyboardButton(
            text=t(f"greeting.tone.{tone}", lang),
            callback_data=TemplateCallback(action="pick", value=tone, event_id=event_id).pack(),
        )
        for tone in _TONES
    ]
    ai_btn = InlineKeyboardButton(
        text=t("greeting.tone.ai", lang),
        callback_data=TemplateCallback(action="ai", event_id=event_id).pack(),
    )
    personal_btn = InlineKeyboardButton(
        text=t("greeting.tone.personal", lang),
        callback_data=TemplateCallback(action="list", event_id=event_id).pack(),
    )
    back_btn = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=EventCallback(action="v", event_id=event_id).pack(),
    )
    rows = [buttons[:2], buttons[2:], [ai_btn, personal_btn], [back_btn]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def greeting_result_keyboard(
    lang: str,
    event_id: int,
    tone: str,
    last_tpl_id: int,
    greeting_text: str,
) -> InlineKeyboardMarkup:
    """S14 result — another / share / back."""
    another_btn = InlineKeyboardButton(
        text=t("greeting.another", lang),
        callback_data=TemplateCallback(
            action="pick", value=tone, event_id=event_id, exclude_id=last_tpl_id
        ).pack(),
    )
    # switch_inline_query sends the greeting text into a chat the user picks
    share_btn = InlineKeyboardButton(
        text=t("greeting.share", lang),
        switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
            query=greeting_text,
            allow_user_chats=True,
            allow_bot_chats=False,
            allow_group_chats=True,
            allow_channel_chats=False,
        ),
    )
    back_btn = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=TemplateCallback(action="style", event_id=event_id, value=None).pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[another_btn, share_btn], [back_btn]])


def ai_prompt_keyboard(lang: str, event_id: int) -> InlineKeyboardMarkup:
    """Shown under the copy-paste AI prompt — just a way back to the tone picker."""
    back_btn = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=TemplateCallback(action="style", event_id=event_id).pack(),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[back_btn]])


def personal_templates_keyboard(
    lang: str, event_id: int, templates: list[tuple[int, str]]
) -> InlineKeyboardMarkup:
    """S14 "✏️ שלי" — one row per personal template with a delete button."""
    rows = [
        [
            InlineKeyboardButton(
                text=preview,
                callback_data=TemplateCallback(
                    action="use", value=str(tpl_id), event_id=event_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=TemplateCallback(
                    action="del", value=str(tpl_id), event_id=event_id
                ).pack(),
            ),
        ]
        for tpl_id, preview in templates
    ]
    new_btn = InlineKeyboardButton(
        text=t("greeting.new.create", lang),
        callback_data=TemplateCallback(action="new", event_id=event_id).pack(),
    )
    back_btn = InlineKeyboardButton(
        text=t("common.back", lang),
        callback_data=TemplateCallback(action="style", event_id=event_id).pack(),
    )
    rows.append([new_btn])
    rows.append([back_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def template_new_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard shown when creating a new personal template."""
    tones = [
        InlineKeyboardButton(
            text=t(f"greeting.tone.{tone}", lang),
            callback_data=TemplateCallback(action="new_tone", value=tone).pack(),
        )
        for tone in _TONES
    ]
    cancel_btn = InlineKeyboardButton(
        text=t("common.cancel", lang), callback_data=NavCallback(action="cancel").pack()
    )
    rows = [tones[:2], tones[2:], [cancel_btn]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
