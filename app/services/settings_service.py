from __future__ import annotations

from zoneinfo import available_timezones

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class InvalidTimezoneError(Exception):
    """Raised when a user-typed IANA timezone name doesn't exist."""


_VALID_TIMEZONES = available_timezones()


async def update_setting(session: AsyncSession, user: User, **fields: object) -> User:
    """Apply one or more settings fields and persist immediately (SPEC.md ch.20:
    "שינוי נשמר מיד — אין 'שמור'")."""
    for key, value in fields.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


def validate_timezone(tz: str) -> str:
    cleaned = tz.strip()
    if cleaned not in _VALID_TIMEZONES:
        raise InvalidTimezoneError(cleaned)
    return cleaned


async def wipe_account(session: AsyncSession, user: User) -> None:
    """Permanently delete the user row — CASCADE removes events, rules, etc."""
    await session.delete(user)
    await session.commit()
