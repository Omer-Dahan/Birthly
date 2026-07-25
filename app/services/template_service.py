"""Template (greeting) service. See SPEC.md chapter 22.

Selects a random greeting template, renders placeholders, and manages
personal template CRUD.  This module has no aiogram dependency.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import age_at
from app.core.formatting import format_name
from app.db.models import Event, GreetingTemplate, User
from app.db.repositories.templates import TemplateRepository
from app.i18n.translator import t
from app.services.clock import user_today
from app.services.event_card_service import event_type_label
from app.services.exceptions import LimitError, NotFoundError

_USER_TEMPLATE_LIMIT = 20
_SENTENCE_RE = re.compile(r"[^.!?。]*\{age\}[^.!?。]*[.!?。]?")


# ── public API ─────────────────────────────────────────────────────────────


async def pick_template(
    session: AsyncSession,
    user: User,
    event: Event,
    tone: str,
    *,
    exclude_id: int | None = None,
) -> GreetingTemplate | None:
    """Return a randomly-chosen template for (event_type, tone, gender, language).

    When ``exclude_id`` is provided the previously shown template is avoided
    so the same text never appears twice in a row.  Returns ``None`` if no
    template matches at all (should not happen in a fully-seeded DB).
    """
    repo = TemplateRepository(session, user.id)
    candidates = await repo.list_matching(
        event_type=event.event_type,
        tone=tone,
        gender=event.gender,
        language=user.language,
    )
    if not candidates:
        return None

    # Try to avoid repeating the last one shown.
    if exclude_id is not None and len(candidates) > 1:
        candidates = [c for c in candidates if c.id != exclude_id] or candidates

    return random.choice(candidates)


def render_template(tpl: GreetingTemplate, event: Event, user: User) -> str:
    """Replace placeholders in ``tpl.body`` with event-specific values.

    Missing values are handled gracefully:
    - ``{age}`` missing  → entire sentence containing the placeholder is removed.
    - ``{nickname}``     → falls back to first_name.
    - ``{relation}``     → omitted (replaced with empty string).
    """
    today = user_today(user)
    age = age_at(event.calendar_type, event.year, event.month, event.day, today)

    body = tpl.body

    # {age} — if no age, drop the whole sentence that contains it.
    if age is not None:
        body = body.replace("{age}", str(age))
    else:
        body = _SENTENCE_RE.sub("", body).strip()

    # {name}
    body = body.replace("{name}", format_name(event.first_name, event.last_name))

    # {nickname} — fallback to first_name
    nickname = event.nickname or event.first_name
    body = body.replace("{nickname}", nickname)

    # {relation} — optional, silently drop placeholder if absent
    relation = event.relation or ""
    body = body.replace("{relation}", relation)

    return body.strip()


async def create_user_template(
    session: AsyncSession,
    user: User,
    *,
    event_type: str,
    tone: str,
    gender: str | None,
    body: str,
) -> GreetingTemplate:
    """Create a personal template for the user (max 20, SPEC.md §22)."""
    repo = TemplateRepository(session, user.id)
    count = await repo.count_user_templates()
    if count >= _USER_TEMPLATE_LIMIT:
        raise LimitError(f"user template limit ({_USER_TEMPLATE_LIMIT}) reached")

    tpl = GreetingTemplate(
        user_id=user.id,
        event_type=event_type,
        tone=tone,
        gender=gender,
        language=user.language,
        body=body,
        is_active=True,
    )
    return await repo.create(tpl)


async def delete_user_template(
    session: AsyncSession,
    user: User,
    template_id: int,
) -> None:
    """Soft-delete a personal template owned by this user."""
    repo = TemplateRepository(session, user.id)
    tpl = await repo.get_owned(template_id)
    if tpl is None or tpl.user_id is None:
        raise NotFoundError(f"template {template_id} not found for user {user.id}")
    await repo.delete(tpl)


@dataclass(frozen=True)
class RenderResult:
    template_id: int
    text: str


def build_ai_prompt(event: Event, user: User, tone: str) -> str:
    """Build a copy-paste prompt the user hands to their own AI assistant,
    instead of picking a pre-written template (SPEC.md §22 / S14 "AI" option).

    Fills in whatever the event card actually has — name, event type, tone,
    age/anniversary-years if known, relation/nickname if set, and free-text
    notes — and leaves the rest to the AI. The bot never calls an AI itself;
    it only prepares text for the user to paste elsewhere.
    """
    lang = user.language
    name = format_name(event.first_name, event.last_name)
    type_label = event_type_label(event.event_type, lang)
    tone_label = t(f"greeting.tone.{tone}", lang)

    today = user_today(user)
    age = age_at(event.calendar_type, event.year, event.month, event.day, today)

    details = [f"שם: {name}", f"סוג אירוע: {type_label}", f"טון מבוקש: {tone_label}"]
    if age is not None:
        details.append(f"גיל/שנים: {age}")
    if event.relation:
        details.append(f"קשר: {event.relation}")
    if event.nickname:
        details.append(f"כינוי: {event.nickname}")
    if event.notes:
        details.append(f"הערות: {event.notes}")

    details_block = "\n".join(f"- {line}" for line in details)
    return (
        "כתוב עבורי ברכה קצרה וחמה בעברית, על סמך הפרטים הבאים:\n\n"
        f"{details_block}\n\n"
        "אנא תכתוב ברכה מוכנה, בלי הסברים נוספים."
    )
