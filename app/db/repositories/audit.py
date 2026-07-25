from __future__ import annotations

import json
from typing import Any

from app.db.models import AuditLog
from app.db.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def add(
        self,
        action: str,
        entity: str,
        entity_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Add an audit log entry."""
        log = AuditLog(
            user_id=self.user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload=json.dumps(payload, ensure_ascii=False) if payload else None,
        )
        self.session.add(log)
        await self.session.flush()
        return log
