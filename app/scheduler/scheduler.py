"""Scheduler bootstrap — build and configure APScheduler.

Call ``build_scheduler(bot, session_factory)`` once during startup (main.py).
The returned ``AsyncIOScheduler`` must be started before polling begins and
shut down gracefully on SIGTERM via ``scheduler.shutdown(wait=True)``.

Job rules (SPEC.md ch.17):
  - max_instances=1    — prevents overlapping runs
  - coalesce=True      — skipped ticks merge into one catch-up run
  - misfire_grace_time — seconds before a missed trigger is discarded
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.scheduler import jobs

logger = logging.getLogger(__name__)

_COMMON_JOB_KWARGS: dict[str, Any] = {
    "max_instances": 1,
    "coalesce": True,
    "misfire_grace_time": 300,
}


def _safe(
    coro_func: Callable[..., Awaitable[None]], name: str
) -> Callable[..., Awaitable[None]]:
    """Wrap a coroutine function so any exception is caught, logged, and NOT re-raised.

    This ensures a crashing job never brings down the scheduler.
    """

    @functools.wraps(coro_func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            await coro_func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "scheduler_job_error",
                extra={"job": name, "error": str(exc)},
                exc_info=True,
            )

    return wrapper


def build_scheduler(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIOScheduler:
    """Create and configure the AsyncIOScheduler with all registered jobs.

    Jobs are NOT started here — call ``scheduler.start()`` after this returns.
    """
    scheduler = AsyncIOScheduler()

    # ── tick_reminders — every SCHEDULER_TICK_SECONDS seconds ─────────────────
    scheduler.add_job(
        _safe(jobs.tick_reminders, "tick_reminders"),
        trigger="interval",
        seconds=settings.scheduler_tick_seconds,
        args=[bot, session_factory],
        id="tick_reminders",
        **_COMMON_JOB_KWARGS,
    )

    # ── recompute_occurrences — daily 02:00 UTC ───────────────────────────────
    scheduler.add_job(
        _safe(jobs.recompute_occurrences, "recompute_occurrences"),
        trigger="cron",
        hour=2,
        minute=0,
        timezone="UTC",
        args=[session_factory],
        id="recompute_occurrences",
        **_COMMON_JOB_KWARGS,
    )

    # ── daily_digest — every 15 minutes ──────────────────────────────────────
    scheduler.add_job(
        _safe(jobs.daily_digest, "daily_digest"),
        trigger="interval",
        minutes=15,
        args=[bot, session_factory],
        id="daily_digest",
        **_COMMON_JOB_KWARGS,
    )

    # ── auto_backup — daily at AUTO_BACKUP_TIME (local server time, treated as UTC) ──
    h, m = settings.auto_backup_time.split(":")
    scheduler.add_job(
        _safe(jobs.auto_backup, "auto_backup"),
        trigger="cron",
        hour=int(h),
        minute=int(m),
        timezone="UTC",
        args=[session_factory],
        id="auto_backup",
        **_COMMON_JOB_KWARGS,
    )

    # ── purge_soft_deleted — daily 04:00 UTC ─────────────────────────────────
    scheduler.add_job(
        _safe(jobs.purge_soft_deleted, "purge_soft_deleted"),
        trigger="cron",
        hour=4,
        minute=0,
        timezone="UTC",
        args=[session_factory],
        id="purge_soft_deleted",
        **_COMMON_JOB_KWARGS,
    )

    # ── cleanup_logs — weekly (Sunday 05:00 UTC) ──────────────────────────────
    scheduler.add_job(
        _safe(jobs.cleanup_logs, "cleanup_logs"),
        trigger="cron",
        day_of_week="sun",
        hour=5,
        minute=0,
        timezone="UTC",
        args=[session_factory],
        id="cleanup_logs",
        **_COMMON_JOB_KWARGS,
    )

    logger.info(
        "scheduler_built",
        extra={
            "job_count": len(scheduler.get_jobs()),
            "tick_seconds": settings.scheduler_tick_seconds,
        },
    )
    return scheduler
