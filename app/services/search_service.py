from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import Category
from app.core.validators import month_number_from_name
from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.i18n.translator import t


def _category_from_query(query: str, lang: str) -> str | None:
    """Resolve free text to a Category value if it matches a category's localized name."""
    cleaned = query.strip()
    for category in Category:
        if t(f"category.{category.value}", lang) == cleaned:
            return category.value
    return None


async def search_events(session: AsyncSession, user: User, query: str) -> list[Event]:
    """S10: resolve the query to a category/month filter if it matches one,
    otherwise fall back to a free-text LIKE search across name/nickname/
    phone/notes/relation.
    """
    repo = EventRepository(session, user.id)

    category = _category_from_query(query, user.language)
    if category is not None:
        return await repo.search(text=None, category=category, month=None)

    month = month_number_from_name(query)
    if month is not None:
        return await repo.search(text=None, category=None, month=month)

    return await repo.search(text=query, category=None, month=None)
