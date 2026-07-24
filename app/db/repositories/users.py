from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    """Not user-scoped like BaseRepository subclasses: users manage their own row."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        *,
        username: str | None,
        first_name: str,
        last_name: str | None,
        is_admin: bool,
    ) -> tuple[User, bool]:
        """Returns (user, created) — ``created`` is True only on first contact."""
        user = await self.get(user_id)
        if user is not None:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_seen_at = datetime.now(UTC)
            await self.session.commit()
            return user, False

        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.commit()
        return user, True

    async def touch_last_seen(self, user: User) -> None:
        user.last_seen_at = datetime.now(UTC)
        await self.session.commit()
