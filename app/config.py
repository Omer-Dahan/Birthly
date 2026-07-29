from __future__ import annotations

import sys
from typing import Annotated

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_admin_ids(v: object) -> list[int]:
    if isinstance(v, str):
        return [int(x.strip()) for x in v.split(",") if x.strip()]
    if isinstance(v, int):
        return [v]
    if isinstance(v, list):
        return [int(x) for x in v]
    return []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str
    bot_username: str
    admin_ids: Annotated[list[int], BeforeValidator(_parse_admin_ids)] = Field(
        default_factory=list
    )

    # Database
    db_path: str = "data/birthly.db"

    # Defaults
    default_language: str = "he"
    default_timezone: str = "Asia/Jerusalem"
    default_notify_time: str = "09:00"
    default_date_format: str = "DD/MM/YYYY"
    default_time_format: str = "24h"

    # Scheduler
    scheduler_tick_seconds: int = 60
    reminder_grace_hours: int = 6
    max_upcoming_days: int = 45

    # Limits
    max_events_per_user: int = 1000
    rate_limit_messages: int = 12
    rate_limit_callbacks: int = 25
    broadcast_rate_per_sec: int = 20
    page_size: int = 8

    # Anti-spam: stricter limits for accounts still within their grace period
    new_account_grace_hours: float = 1.0
    new_account_rate_limit_messages: int = 6
    new_account_rate_limit_callbacks: int = 12

    # Anti-spam: minimum gap between two button taps from the same user, blocks
    # accidental/rapid double-submits on save/confirm/toggle actions
    callback_debounce_ms: int = 400

    # Backup
    auto_backup_enabled: bool = True
    auto_backup_time: str = "03:30"
    backup_retention_days: int = 30
    backup_dir: str = "data/backups"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "data/logs"
    log_json: bool = True
    log_max_bytes: int = 10_485_760
    log_backup_count: int = 5

    # Misc
    env: str = "production"
    report_errors_to_admin: bool = True


def _load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Failed to load configuration: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


settings = _load_settings()
