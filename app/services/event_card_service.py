from __future__ import annotations

from app.constants import Category, EventType
from app.core.dates import age_at, days_until
from app.core.formatting import format_countdown, format_date, format_name, format_phone
from app.core.hebcal import format_hebrew_date, to_hebrew
from app.core.text import esc
from app.db.models import Event, ReminderRule, User
from app.i18n.translator import t
from app.services.clock import user_today
from app.services.reminder_service import summarize_rules

_CATEGORY_KEYS = {c.value: f"category.{c.value}" for c in Category}
_EVENT_TYPE_KEYS = {e.value: f"event_type.{e.value}" for e in EventType}


def render_card_text(user: User, event: Event, rules: list[ReminderRule]) -> str:
    """Renders the S8 event card body. Empty fields are omitted entirely."""
    lang = user.language
    assert event.next_occurrence is not None

    name = esc(format_name(event.first_name, event.last_name))
    header = f"🎂 <b>{name}</b>"
    if event.nickname:
        header += f"  <i>({esc(event.nickname)})</i>"

    lines = [header, ""]

    today = user_today(user)
    if event.calendar_type == "hebrew":
        heb_year = event.year or to_hebrew(event.next_occurrence)[0]
        heb_str = format_hebrew_date(
            heb_year, event.month, event.day, with_year=event.year is not None
        )
        lines.append(f"📅 {format_date(event.next_occurrence, user.date_format)}  ·  {heb_str}")
    else:
        lines.append(f"📅 {format_date(event.next_occurrence, user.date_format)}")

    countdown = format_countdown(days_until(event.next_occurrence, today))
    lines.append(t("card.days_until", lang, countdown=countdown, gender=event.gender))

    age = age_at(event.calendar_type, event.year, event.month, event.day, event.next_occurrence)
    if age is not None:
        age_key = "card.age_memorial" if event.event_type == "memorial" else "card.age"
        lines.append(t(age_key, lang, age=age, gender=event.gender))

    tag_parts = []
    if event.category and event.category != Category.OTHER.value:
        tag_parts.append(t(_CATEGORY_KEYS.get(event.category, event.category), lang))
    if event.relation:
        tag_parts.append(esc(event.relation))
    if tag_parts:
        lines.append(f"🏷 {' · '.join(tag_parts)}")

    if event.phone:
        lines.append(f"📞 {format_phone(event.phone)}")
    if event.telegram_username:
        lines.append(f"💬 @{esc(event.telegram_username)}")
    if event.notes:
        lines.append(f"📝 {esc(event.notes)}")

    reminders_summary = summarize_rules(rules, lang)
    if reminders_summary:
        lines.append("")
        lines.append(t("card.reminders", lang, rules=reminders_summary))

    return "\n".join(lines)


def event_type_label(event_type: str, lang: str) -> str:
    return t(_EVENT_TYPE_KEYS.get(event_type, event_type), lang)


def category_label(category: str, lang: str) -> str:
    return t(_CATEGORY_KEYS.get(category, category), lang)
