from __future__ import annotations

from app.db.models import Event, ReminderRule, User

# ──────────────────────────────────────────────────────────────────────────────
# Reminder text rendering
# ──────────────────────────────────────────────────────────────────────────────

_BIRTHDAY_PREFIXES_HE: dict[int, str] = {
    0: "🎂 <b>היום יום ההולדת של {name}!</b>",
    1: "🎁 מחר יום ההולדת של <b>{name}</b>",
    2: "🎁 בעוד יומיים — יום ההולדת של <b>{name}</b>",
    7: "🥳 בעוד שבוע — יום ההולדת של <b>{name}</b>",
    14: "🗓 בעוד שבועיים — יום ההולדת של <b>{name}</b>",
    30: "🗓 בעוד חודש — יום ההולדת של <b>{name}</b>",
}

_TYPE_EMOJIS_HE: dict[str, str] = {
    "birthday": "🎂",
    "anniversary": "💍",
    "wedding": "💒",
    "memorial": "🕯",
    "custom": "📌",
}

_TYPE_LABELS_HE: dict[str, str] = {
    "birthday": "יום הולדת",
    "anniversary": "יום נישואין",
    "wedding": "יום החתונה",
    "memorial": "אזכרה",
    "custom": "אירוע",
}


def _display_name(event: Event) -> str:
    """Full display name: 'first_name last_name' or just first_name."""
    if event.last_name:
        return f"{event.first_name} {event.last_name}"
    return event.first_name


def _gender_phrase(event: Event, lang: str) -> str:
    """'הוא חוגג' / 'היא חוגגת' / 'חוגג/ת'."""
    if lang == "he":
        if event.gender == "m":
            return "הוא חוגג"
        if event.gender == "f":
            return "היא חוגגת"
        return "חוגג/ת"
    # English fallback
    return "celebrating"


def render_reminder(
    user: User,
    event: Event,
    rule: ReminderRule,
    occurrence_year: int,
) -> str:
    """Build the HTML reminder message text (SPEC.md S16).

    ``occurrence_year`` is the Gregorian year of the next occurrence — used
    to compute the age displayed in the message.
    """
    name = _display_name(event)
    lang = user.language
    offset = rule.offset_days if rule.offset_days is not None else 0
    etype = event.event_type

    # --- header line ---
    if lang == "he":
        if etype == "birthday":
            if offset in _BIRTHDAY_PREFIXES_HE:
                header = _BIRTHDAY_PREFIXES_HE[offset].format(name=name)
            else:
                header = f"📅 בעוד {offset} ימים — יום ההולדת של <b>{name}</b>"
        elif etype == "memorial":
            emoji = _TYPE_EMOJIS_HE["memorial"]
            header = f"{emoji} <b>אזכרה — {name}</b>"
        else:
            emoji = _TYPE_EMOJIS_HE.get(etype, "📌")
            label = event.custom_type_label or _TYPE_LABELS_HE.get(etype, etype)
            header = f"{emoji} <b>{label} — {name}</b>"
    else:
        # English
        header = f"🎂 <b>{name}</b>'s birthday"
        if offset == 1:
            header = f"🎁 Tomorrow is <b>{name}</b>'s birthday"
        elif offset > 1:
            header = f"📅 In {offset} days — <b>{name}</b>'s birthday"

    # --- body lines ---
    lines = [header, ""]

    if etype == "birthday" and event.year is not None:
        age = occurrence_year - event.year
        gender_phrase = _gender_phrase(event, lang)
        if lang == "he":
            lines.append(f"🎈 {gender_phrase} <b>{age}</b>")
        else:
            lines.append(f"🎈 Turning <b>{age}</b>")

    if event.relation and event.category and event.category != "other":
        lines.append(f"🏷 {event.category} · {event.relation}")
    elif event.relation:
        lines.append(f"🏷 {event.relation}")

    if event.phone:
        lines.append(f"📞 {event.phone}")

    return "\n".join(lines)
