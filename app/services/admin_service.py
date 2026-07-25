from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AppMeta, Event, NotificationLog, User
from app.db.repositories.audit import AuditRepository


async def get_system_stats(session: AsyncSession) -> dict[str, Any]:
    # Users
    total_users = await session.scalar(select(func.count()).select_from(User))
    active_users = await session.scalar(
        select(func.count())
        .select_from(User)
        .where(User.last_seen_at >= datetime.now(UTC) - timedelta(days=30))
    )

    # Events
    total_events = await session.scalar(select(func.count()).select_from(Event))

    # Notifications today
    today = datetime.now(UTC).date()
    sent_today = await session.scalar(
        select(func.count())
        .select_from(NotificationLog)
        .where(NotificationLog.status == "sent", NotificationLog.occurrence_date == today)
    )
    failed_today = await session.scalar(
        select(func.count())
        .select_from(NotificationLog)
        .where(NotificationLog.status == "failed", NotificationLog.occurrence_date == today)
    )

    # DB Size
    db_size = 0.0
    if os.path.exists(settings.db_path):
        db_size = os.path.getsize(settings.db_path) / (1024 * 1024)

    # Backup time
    last_backup_meta = await session.scalar(
        select(AppMeta).where(AppMeta.key == "last_auto_backup")
    )
    last_backup = last_backup_meta.value if last_backup_meta else "Never"

    # Scheduler health (SPEC.md ch.33): last successful tick_reminders run
    last_tick_meta = await session.scalar(select(AppMeta).where(AppMeta.key == "last_tick_at"))
    last_tick = last_tick_meta.value if last_tick_meta else "Never"

    return {
        "total_users": total_users or 0,
        "active_users": active_users or 0,
        "total_events": total_events or 0,
        "sent_today": sent_today or 0,
        "failed_today": failed_today or 0,
        "db_size_mb": round(db_size, 2),
        "last_backup": last_backup,
        "last_tick_at": last_tick,
    }


async def get_broadcast_targets(
    session: AsyncSession, admin_id: int, text: str
) -> list[User]:
    """Active, non-blocked users to broadcast to, with the attempt logged to the audit trail.

    Sending itself touches aiogram's Bot, so it stays in the handler layer
    (app/handlers/admin.py) — app/services must stay framework-agnostic.
    """
    users = list(
        (
            await session.scalars(
                select(User).where(
                    User.is_blocked.is_(False), User.bot_blocked_by_user.is_(False)
                )
            )
        ).all()
    )

    audit_repo = AuditRepository(session, admin_id)
    await audit_repo.add(
        "admin_broadcast", "system", payload={"text": text, "target_count": len(users)}
    )
    return users


async def get_user_info(session: AsyncSession, identifier: str) -> dict[str, Any] | None:
    stmt = select(User)
    if identifier.isdigit():
        stmt = stmt.where(User.id == int(identifier))
    else:
        username = identifier.lstrip("@")
        stmt = stmt.where(func.lower(User.username) == username.lower())

    user = await session.scalar(stmt)
    if not user:
        return None

    events_count = await session.scalar(
        select(func.count()).select_from(Event).where(Event.user_id == user.id)
    )

    return {
        "id": user.id,
        "name": f"{user.first_name} {user.last_name or ''}".strip(),
        "username": user.username,
        "events_count": events_count or 0,
        "created_at": user.created_at,
        "last_seen_at": user.last_seen_at,
        "is_blocked": user.is_blocked,
        "bot_blocked": user.bot_blocked_by_user,
    }


async def toggle_block_user(
    session: AsyncSession, admin_id: int, user_id: int, block: bool
) -> bool:
    user = await session.get(User, user_id)
    if not user:
        return False

    user.is_blocked = block

    audit_repo = AuditRepository(session, admin_id)
    action = "user_blocked" if block else "user_unblocked"
    await audit_repo.add(action, "users", entity_id=user.id)
    await session.commit()
    return True


async def force_backup(session: AsyncSession, admin_id: int) -> str:
    from sqlalchemy import text

    audit_repo = AuditRepository(session, admin_id)

    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"birthly_manual_{now_str}.db"

    await session.execute(text(f"VACUUM INTO '{backup_path.resolve()}'"))
    await audit_repo.add(
        "export",
        "system",
        payload={"format": "db", "type": "manual_vacuum", "path": str(backup_path)},
    )
    await session.commit()

    return str(backup_path)


def get_recent_logs(n: int = 50) -> str:
    log_file = Path(settings.log_dir) / "bot.log"
    if not log_file.exists():
        return "Log file not found."

    try:
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except Exception as e:
        return f"Error reading logs: {e}"
