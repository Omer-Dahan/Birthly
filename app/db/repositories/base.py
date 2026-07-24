from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelT]:
    """User-scoped repository base. Every query is filtered by ``user_id``.

    There is deliberately no method that fetches a row by ``id`` alone —
    see SPEC.md chapter 27 (IDOR protection).
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession, user_id: int) -> None:
        self.session = session
        self.user_id = user_id

    async def get_owned(self, entity_id: int) -> ModelT | None:
        """Fetch a row by id, scoped to this repository's user_id. None if not found/owned."""
        stmt = select(self.model).where(
            self.model.id == entity_id,  # type: ignore[attr-defined]
            self.model.user_id == self.user_id,  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _base_query(self) -> Any:
        return select(self.model).where(self.model.user_id == self.user_id)  # type: ignore[attr-defined]
