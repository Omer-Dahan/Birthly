"""Repository for greeting_templates.

System templates (user_id IS NULL) are readable by everyone; personal
templates are scoped to their owner. See SPEC.md chapter 22.
"""

from __future__ import annotations

from sqlalchemy import or_, select

from app.db.models import GreetingTemplate
from app.db.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[GreetingTemplate]):
    model = GreetingTemplate

    # ── read ──────────────────────────────────────────────────────────────

    async def list_matching(
        self,
        event_type: str,
        tone: str,
        gender: str | None,
        language: str,
    ) -> list[GreetingTemplate]:
        """Return all active templates that match the query.

        Includes both system templates (user_id IS NULL) and the current
        user's personal templates.  Gender=None matches neutral + specific.
        """
        stmt = (
            select(GreetingTemplate)
            .where(
                GreetingTemplate.is_active.is_(True),
                GreetingTemplate.event_type == event_type,
                GreetingTemplate.tone == tone,
                GreetingTemplate.language == language,
                or_(
                    GreetingTemplate.user_id.is_(None),
                    GreetingTemplate.user_id == self.user_id,
                ),
            )
            .order_by(GreetingTemplate.id)
        )
        if gender:
            stmt = stmt.where(
                or_(
                    GreetingTemplate.gender.is_(None),
                    GreetingTemplate.gender == gender,
                )
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_user_templates(self) -> list[GreetingTemplate]:
        """All personal templates belonging to this user (any type/tone)."""
        stmt = (
            self._base_query()
            .where(GreetingTemplate.is_active.is_(True))
            .order_by(GreetingTemplate.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_templates(self) -> int:
        """Count of personal templates (for the 20-template limit check)."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(
            self._base_query().where(GreetingTemplate.is_active.is_(True)).subquery()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ── write ─────────────────────────────────────────────────────────────

    async def create(self, template: GreetingTemplate) -> GreetingTemplate:
        """Persist a new personal template."""
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete(self, template: GreetingTemplate) -> None:
        """Soft-delete: mark as inactive (keeps history intact)."""
        template.is_active = False
        await self.session.commit()
