"""Backup, export, and import service. See SPEC.md chapter 23.

Export formats:
  - JSON  — full round-trip format (user settings + events + rules + templates)
  - CSV   — events only, UTF-8 with BOM, Hebrew column headers
  - XLSX  — events sheet + summary sheet, RTL

Import:
  - Only JSON is supported as an import format.
  - Duplicate detection by (first_name, last_name, month, day, calendar_type).
  - Bad rows accumulate into an ImportResult; they never abort the import.

System backup:
  - VACUUM INTO for safe hot-backup.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import next_occurrence
from app.db.models import Event, GreetingTemplate, ReminderRule, User
from app.db.repositories.events import EventRepository
from app.db.repositories.reminders import ReminderRuleRepository
from app.db.repositories.templates import TemplateRepository
from app.services.clock import user_today

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = 1

# CSV column headers (Hebrew, per SPEC)
_CSV_HEADERS = [
    "שם פרטי",
    "שם משפחה",
    "כינוי",
    "תאריך (יום)",
    "תאריך (חודש)",
    "תאריך (שנה)",
    "לוח",
    "סוג אירוע",
    "קטגוריה",
    "קשר",
    "מין",
    "טלפון",
    "טלגרם",
    "הערות",
    "שעת אירוע",
    "פעיל",
]


# ── export ─────────────────────────────────────────────────────────────────


async def export_json(session: AsyncSession, user: User) -> bytes:
    """Export all user data as a JSON blob suitable for re-import."""
    event_repo = EventRepository(session, user.id)
    rule_repo = ReminderRuleRepository(session, user.id)
    tpl_repo = TemplateRepository(session, user.id)

    events = await event_repo.list_not_deleted()
    global_rules = await rule_repo.list_global()
    templates = await tpl_repo.list_user_templates()

    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "user": {
            "language": user.language,
            "timezone": user.timezone,
            "date_format": user.date_format,
            "time_format": user.time_format,
            "default_notify_time": user.default_notify_time,
            "show_hebrew_date": user.show_hebrew_date,
            "daily_digest_enabled": user.daily_digest_enabled,
            "digest_time": user.digest_time,
            "adar_policy": user.adar_policy,
            "feb29_policy": user.feb29_policy,
        },
        "events": [_event_to_dict_sync(e) for e in events],
        "global_reminder_rules": [_rule_to_dict(r) for r in global_rules],
        "personal_templates": [_tpl_to_dict(t) for t in templates],
    }

    # Per-event rules need a separate pass (we can't await inside the dict literal above).
    for i, event in enumerate(events):
        per_event_rules = await rule_repo.list_for_event(event.id)
        payload["events"][i]["reminder_rules"] = [_rule_to_dict(r) for r in per_event_rules]

    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


async def export_csv(session: AsyncSession, user: User) -> bytes:
    """Export events as CSV with UTF-8 BOM and Hebrew headers."""
    repo = EventRepository(session, user.id)
    events = await repo.list_not_deleted()

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM
    writer = csv.writer(buf)
    writer.writerow(_CSV_HEADERS)
    for event in events:
        writer.writerow(
            [
                event.first_name,
                event.last_name or "",
                event.nickname or "",
                event.day,
                event.month,
                event.year or "",
                "עברי" if event.calendar_type == "hebrew" else "לועזי",
                event.event_type,
                event.category,
                event.relation or "",
                event.gender or "",
                event.phone or "",
                event.telegram_username or "",
                event.notes or "",
                event.event_time or "",
                "כן" if event.is_active else "לא",
            ]
        )
    return buf.getvalue().encode("utf-8")


async def export_xlsx(session: AsyncSession, user: User) -> bytes:
    """Export events as an XLSX workbook with an events sheet and a summary sheet."""
    try:
        import openpyxl  # type: ignore
        from openpyxl.styles import Font  # type: ignore
    except ImportError as exc:
        raise RuntimeError("openpyxl is required for XLSX export") from exc

    repo = EventRepository(session, user.id)
    events = await repo.list_not_deleted()

    wb = openpyxl.Workbook()

    # ── events sheet ──
    ws_events = wb.active
    ws_events.title = "אירועים"
    ws_events.sheet_view.rightToLeft = True

    ws_events.append(_CSV_HEADERS)
    for cell in ws_events[1]:
        cell.font = Font(bold=True)

    for event in events:
        ws_events.append(
            [
                event.first_name,
                event.last_name or "",
                event.nickname or "",
                event.day,
                event.month,
                event.year or "",
                "עברי" if event.calendar_type == "hebrew" else "לועזי",
                event.event_type,
                event.category,
                event.relation or "",
                event.gender or "",
                event.phone or "",
                event.telegram_username or "",
                event.notes or "",
                event.event_time or "",
                "כן" if event.is_active else "לא",
            ]
        )

    # Auto-width (approximate)
    for col in ws_events.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=8)
        ws_events.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    # ── summary sheet ──
    ws_summary = wb.create_sheet("סיכום")
    ws_summary.sheet_view.rightToLeft = True
    total = len(events)
    active = sum(1 for e in events if e.is_active)
    ws_summary.append(['סה"כ אירועים', total])
    ws_summary.append(["פעילים", active])
    ws_summary.append(["מושתקים", total - active])
    ws_summary.append(["יוצא בתאריך", datetime.now(UTC).strftime("%d/%m/%Y %H:%M")])

    buf = io.BytesIO()
    # openpyxl is blocking I/O — offload to thread
    await asyncio.to_thread(wb.save, buf)
    return buf.getvalue()


# ── import ─────────────────────────────────────────────────────────────────


@dataclass
class ImportResult:
    total_parsed: int = 0
    imported: int = 0
    duplicates: int = 0
    errors: list[str] = field(default_factory=list)


async def parse_import_json(data: bytes) -> tuple[dict[str, Any], ImportResult]:
    """Parse raw bytes into a validated import payload dict.

    Returns ``(payload, result)`` where result.errors lists parse problems.
    Raises ``ValueError`` if the bytes are not valid JSON at all.
    """
    result = ImportResult()
    payload = json.loads(data.decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("root element must be a JSON object")

    events_raw = payload.get("events", [])
    if not isinstance(events_raw, list):
        raise ValueError("'events' must be a list")

    result.total_parsed = len(events_raw)
    return payload, result


async def do_import(
    session: AsyncSession,
    user: User,
    payload: dict[str, Any],
    *,
    mode: str = "add",
) -> ImportResult:
    """Execute the import.

    ``mode`` is ``'add'`` (merge) or ``'replace'`` (delete all first).
    Duplicate detection key: (first_name, last_name, month, day, calendar_type).
    Bad rows are accumulated into result.errors, never abort the import.
    """
    result = ImportResult()
    events_raw: list[dict[str, Any]] = payload.get("events", [])
    result.total_parsed = len(events_raw)

    repo = EventRepository(session, user.id)
    today = user_today(user)

    if mode == "replace":
        existing = await repo.list_not_deleted()
        for ev in existing:
            await repo.soft_delete(ev)

    existing_events = await repo.list_not_deleted()
    dup_keys: set[tuple[Any, ...]] = {
        (e.first_name.lower(), (e.last_name or "").lower(), e.month, e.day, e.calendar_type)
        for e in existing_events
    }

    for i, raw in enumerate(events_raw, start=1):
        try:
            event = _dict_to_event(raw, user.id, today, user)
        except Exception as exc:
            result.errors.append(f"row {i}: {exc}")
            continue

        dup_key = (
            event.first_name.lower(),
            (event.last_name or "").lower(),
            event.month,
            event.day,
            event.calendar_type,
        )
        if dup_key in dup_keys:
            result.duplicates += 1
            continue

        dup_keys.add(dup_key)
        session.add(event)
        result.imported += 1

    await session.commit()
    return result


# ── system backup ──────────────────────────────────────────────────────────


async def auto_backup(db_path: str, backup_dir: str, retention_days: int) -> Path:
    """Create a hot backup using VACUUM INTO and prune old backups.

    Safe to call while the bot is running (SQLite WAL mode).
    Returns the path of the new backup file.
    """
    backup_dir_path = Path(backup_dir)
    backup_dir_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d")
    dest = backup_dir_path / f"birthly_{timestamp}.db"

    if dest.exists():
        # Already backed up today — skip
        return dest

    await asyncio.to_thread(_vacuum_into, db_path, str(dest))

    # Prune old backups
    cutoff = datetime.now(UTC).timestamp() - retention_days * 86400
    for p in backup_dir_path.glob("birthly_*.db"):
        if p.stat().st_mtime < cutoff:
            try:
                p.unlink()
            except OSError:
                logger.warning("backup_prune_failed", extra={"path": str(p)})

    return dest


def _vacuum_into(src: str, dest: str) -> None:
    """Blocking helper: runs VACUUM INTO in a thread so it won't block the loop."""
    import sqlite3

    con = sqlite3.connect(src)
    try:
        con.execute(f"VACUUM INTO '{dest}'")
    finally:
        con.close()


# ── private helpers ────────────────────────────────────────────────────────


def _event_to_dict_sync(event: Event) -> dict[str, Any]:
    return {
        "first_name": event.first_name,
        "last_name": event.last_name,
        "nickname": event.nickname,
        "month": event.month,
        "day": event.day,
        "year": event.year,
        "calendar_type": event.calendar_type,
        "event_type": event.event_type,
        "custom_type_label": event.custom_type_label,
        "category": event.category,
        "gender": event.gender,
        "relation": event.relation,
        "phone": event.phone,
        "telegram_username": event.telegram_username,
        "notes": event.notes,
        "event_time": event.event_time,
        "is_active": event.is_active,
        # photo_file_id intentionally omitted (SPEC §23)
        "reminder_rules": [],  # filled in by caller
    }


def _rule_to_dict(rule: ReminderRule) -> dict[str, Any]:
    return {
        "offset_days": rule.offset_days,
        "offset_minutes": rule.offset_minutes,
        "send_time": rule.send_time,
        "enabled": rule.enabled,
    }


def _tpl_to_dict(tpl: GreetingTemplate) -> dict[str, Any]:
    return {
        "event_type": tpl.event_type,
        "tone": tpl.tone,
        "gender": tpl.gender,
        "language": tpl.language,
        "body": tpl.body,
    }


def _dict_to_event(raw: dict[str, Any], user_id: int, today: date, user: User) -> Event:
    """Convert a raw dict (from JSON) to an Event object. Raises on invalid data."""
    first_name = str(raw.get("first_name") or "").strip()
    if not first_name:
        raise ValueError("missing first_name")

    month = int(raw["month"])
    day = int(raw["day"])

    if not (1 <= month <= 13):
        raise ValueError(f"invalid month: {month}")
    if not (1 <= day <= 31):
        raise ValueError(f"invalid day: {day}")

    year = raw.get("year")
    if year is not None:
        year = int(year)

    calendar_type = raw.get("calendar_type", "gregorian")
    if calendar_type not in ("gregorian", "hebrew"):
        raise ValueError(f"invalid calendar_type: {calendar_type}")

    event_type = raw.get("event_type", "birthday")
    if event_type not in ("birthday", "anniversary", "wedding", "memorial", "custom"):
        raise ValueError(f"invalid event_type: {event_type}")

    category = raw.get("category", "other")
    if category not in ("family", "friends", "work", "clients", "school", "other"):
        category = "other"

    occ = next_occurrence(
        calendar_type,
        year,
        month,
        day,
        today,
        adar_policy=user.adar_policy,
        feb29_policy=user.feb29_policy,
    )

    return Event(
        user_id=user_id,
        first_name=first_name,
        last_name=raw.get("last_name") or None,
        nickname=raw.get("nickname") or None,
        month=month,
        day=day,
        year=year,
        calendar_type=calendar_type,
        event_type=event_type,
        custom_type_label=raw.get("custom_type_label") or None,
        category=category,
        gender=raw.get("gender") or None,
        relation=raw.get("relation") or None,
        phone=raw.get("phone") or None,
        telegram_username=raw.get("telegram_username") or None,
        notes=raw.get("notes") or None,
        event_time=raw.get("event_time") or None,
        is_active=bool(raw.get("is_active", True)),
        next_occurrence=occ,
    )
