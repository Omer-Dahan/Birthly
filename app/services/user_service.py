from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReminderRule, User
from app.db.repositories.users import UserRepository


async def get_or_create_user(
    session: AsyncSession,
    *,
    user_id: int,
    username: str | None,
    first_name: str,
    last_name: str | None,
    is_admin: bool,
) -> User:
    """Fetch the user's row, creating it on first contact. Refreshes profile fields.

    A brand-new user gets two default global reminder rules (SPEC.md chapter
    8): "the day before" and "the day of", both at the user's default time.
    """
    repo = UserRepository(session)
    user, created = await repo.get_or_create(
        user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin,
    )

    if created:
        session.add_all(
            [
                ReminderRule(user_id=user.id, offset_days=1),
                ReminderRule(user_id=user.id, offset_days=0),
            ]
        )
        await session.commit()

    return user


async def set_language(session: AsyncSession, user: User, language: str) -> None:
    user.language = language
    await session.commit()


async def set_timezone(session: AsyncSession, user: User, timezone: str) -> None:
    user.timezone = timezone
    await session.commit()


async def set_default_notify_time(session: AsyncSession, user: User, hhmm: str) -> None:
    user.default_notify_time = hhmm
    await session.commit()


async def complete_onboarding(session: AsyncSession, user: User) -> None:
    user.onboarded = True
    await session.commit()
