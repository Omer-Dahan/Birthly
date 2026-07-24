"""CallbackData factories. See SPEC.md chapter 13 for the full schema.

Every callback_data string in the bot must come from one of these factories,
never a hand-built string, so payloads stay within Telegram's 64-byte limit
and stay structurally validated.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="mnu"):
    action: str  # home | add | list | rem | set | srch | stat | help


class NavCallback(CallbackData, prefix="nav"):
    action: str  # back | home | cancel


class NoopCallback(CallbackData, prefix="noop"):
    pass


class EventFlowCallback(CallbackData, prefix="ev"):
    """Add/edit-flow actions with no event id yet: type, heb, hm, hd, gm, gd,
    noyear, cat, gender, more, field, clear, skip, save, cancel."""

    action: str
    value: str | None = None


class EventCallback(CallbackData, prefix="ev"):
    """Card-scoped actions on an existing, owned event: v, e, d, dy, undo,
    gr, sh, rem, mute."""

    action: str
    event_id: int


class ListCallback(CallbackData, prefix="ls"):
    action: str  # p | sort | filt | fset | view
    value: str


class ReminderCallback(CallbackData, prefix="rem"):
    action: str  # add | off | time | tog | del
    value: str | None = None
    event_id: int | None = None


class SettingsCallback(CallbackData, prefix="set"):
    action: str
    value: str | None = None


class StatsCallback(CallbackData, prefix="st"):
    action: str  # home | months | cats | ages


class TemplateCallback(CallbackData, prefix="tpl"):
    action: str  # list | v | new | del | use
    value: str | None = None
    event_id: int | None = None


class BackupCallback(CallbackData, prefix="bk"):
    action: str  # home | exp | imp | auto
    value: str | None = None


class AdminCallback(CallbackData, prefix="adm"):
    action: str  # home | stats | bc | bc_ok | logs | u
    value: str | None = None
