from __future__ import annotations

from app.db.models import ReminderRule, User

_OFFSET_LABELS_HE: dict[int, str] = {
    0: "ביום עצמו",
    1: "יום לפני",
    2: "יומיים לפני",
    3: "3 ימים לפני",
    7: "שבוע לפני",
    14: "שבועיים לפני",
    30: "חודש לפני",
}

_OFFSET_LABELS_EN: dict[int, str] = {
    0: "the day of",
    1: "the day before",
    2: "2 days before",
    3: "3 days before",
    7: "a week before",
    14: "two weeks before",
    30: "a month before",
}


def offset_label(offset_days: int, lang: str) -> str:
    labels = _OFFSET_LABELS_HE if lang == "he" else _OFFSET_LABELS_EN
    return labels.get(offset_days, f"{offset_days}d")


def _describe(label: str, send_time: str, lang: str) -> str:
    if lang == "he":
        return f"{label}, ב-{send_time}"
    return f"{label}, at {send_time}"


def describe_rule(rule: ReminderRule, user: User) -> str:
    """e.g. 'יום לפני, ב-09:00' — used in confirmations and card summaries."""
    send_time = rule.send_time or user.default_notify_time
    if rule.offset_days is None:
        return send_time
    label = offset_label(rule.offset_days, user.language)
    return _describe(label, send_time, user.language)


def describe_default_reminder(user: User) -> str:
    """The confirmation text shown right after adding an event (S5): describes
    the "day before" default rule every new user starts with.
    """
    label = offset_label(1, user.language)
    return _describe(label, user.default_notify_time, user.language)
