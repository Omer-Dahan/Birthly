from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select

from app.db.models import Event
from app.db.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    async def count_not_deleted(self) -> int:
        """Count of events that count toward MAX_EVENTS_PER_USER (excludes trash only)."""
        stmt = select(func.count()).select_from(
            self._base_query().where(Event.deleted_at.is_(None)).subquery()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_not_deleted(self) -> list[Event]:
        """All events that are NOT in the trash (used for export)."""
        stmt = self._base_query().where(Event.deleted_at.is_(None)).order_by(Event.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self) -> list[Event]:
        stmt = self._base_query().where(
            Event.deleted_at.is_(None),
            Event.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upcoming_between(self, start: date, end: date) -> list[Event]:
        stmt = (
            self._base_query()
            .where(
                Event.deleted_at.is_(None),
                Event.is_active.is_(True),
                Event.next_occurrence.is_not(None),
                Event.next_occurrence >= start,
                Event.next_occurrence <= end,
            )
            .order_by(Event.next_occurrence)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_page(
        self, *, sort: str, page: int, page_size: int, view: str = "upcoming"
    ) -> tuple[list[Event], int]:
        """Returns (events for this page, total count) for the given view/sort.

        ``view``: upcoming (active, not deleted) | all (not deleted, incl. muted) |
        muted (is_active=False) | trash (soft-deleted).
        """
        stmt = self._base_query()

        if view == "trash":
            stmt = stmt.where(Event.deleted_at.is_not(None))
        else:
            stmt = stmt.where(Event.deleted_at.is_(None))
            if view == "upcoming":
                stmt = stmt.where(Event.is_active.is_(True))
            elif view == "muted":
                stmt = stmt.where(Event.is_active.is_(False))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        if sort == "name":
            stmt = stmt.order_by(Event.first_name, Event.last_name)
        elif sort == "created":
            stmt = stmt.order_by(Event.created_at.desc())
        elif sort == "age":
            stmt = stmt.order_by(Event.year.is_(None), Event.year)
        else:  # upcoming (default)
            stmt = stmt.order_by(Event.next_occurrence.is_(None), Event.next_occurrence)

        stmt = stmt.limit(page_size).offset(page * page_size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def search(
        self, *, text: str | None, category: str | None, month: int | None
    ) -> list[Event]:
        """S10 free-text search: LIKE on name/nickname/phone/notes/relation,
        or filter by resolved category/month (SPEC.md 15/S10).

        ``text`` and (``category`` or ``month``) are mutually exclusive per
        the caller's own resolution — this just applies whichever is given.
        """
        stmt = self._base_query().where(Event.deleted_at.is_(None))

        if category is not None:
            stmt = stmt.where(Event.category == category)
        elif month is not None:
            stmt = stmt.where(Event.month == month)
        elif text is not None:
            like = f"%{text}%"
            stmt = stmt.where(
                or_(
                    Event.first_name.ilike(like),
                    Event.last_name.ilike(like),
                    Event.nickname.ilike(like),
                    Event.phone.ilike(like),
                    Event.notes.ilike(like),
                    Event.relation.ilike(like),
                )
            )

        stmt = stmt.order_by(Event.next_occurrence.is_(None), Event.next_occurrence)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def update(self, event: Event) -> Event:
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def soft_delete(self, event: Event) -> None:
        event.deleted_at = datetime.now(UTC)
        await self.session.commit()

    async def restore(self, event: Event) -> None:
        event.deleted_at = None
        await self.session.commit()

    async def purge_deleted_before(self, cutoff: datetime) -> int:
        stmt = self._base_query().where(Event.deleted_at.is_not(None), Event.deleted_at < cutoff)
        result = await self.session.execute(stmt)
        events = list(result.scalars().all())
        for event in events:
            await self.session.delete(event)
        await self.session.commit()
        return len(events)
