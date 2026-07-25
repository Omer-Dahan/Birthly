from __future__ import annotations

from app.db.models import ReminderRule
from app.db.repositories.base import BaseRepository


class ReminderRuleRepository(BaseRepository[ReminderRule]):
    model = ReminderRule

    async def list_global(self) -> list[ReminderRule]:
        stmt = self._base_query().where(ReminderRule.event_id.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_event(self, event_id: int) -> list[ReminderRule]:
        stmt = self._base_query().where(ReminderRule.event_id == event_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_global(self) -> int:
        return len(await self.list_global())

    async def count_for_event(self, event_id: int) -> int:
        return len(await self.list_for_event(event_id))

    async def create(self, rule: ReminderRule) -> ReminderRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, rule: ReminderRule) -> None:
        await self.session.delete(rule)
        await self.session.commit()

    async def update(self, rule: ReminderRule) -> ReminderRule:
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def toggle(self, rule: ReminderRule) -> ReminderRule:
        rule.enabled = not rule.enabled
        await self.session.commit()
        await self.session.refresh(rule)
        return rule
