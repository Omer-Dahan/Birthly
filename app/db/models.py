from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(default=None)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str | None] = mapped_column(default=None)
    language: Mapped[str] = mapped_column(default="he", server_default="he")
    timezone: Mapped[str] = mapped_column(
        default="Asia/Jerusalem", server_default="Asia/Jerusalem"
    )
    date_format: Mapped[str] = mapped_column(default="DD/MM/YYYY", server_default="DD/MM/YYYY")
    time_format: Mapped[str] = mapped_column(default="24h", server_default="24h")
    default_notify_time: Mapped[str] = mapped_column(default="09:00", server_default="09:00")
    notifications_enabled: Mapped[bool] = mapped_column(default=True, server_default="1")
    silent_notifications: Mapped[bool] = mapped_column(default=False, server_default="0")
    show_hebrew_date: Mapped[bool] = mapped_column(default=True, server_default="1")
    daily_digest_enabled: Mapped[bool] = mapped_column(default=False, server_default="0")
    digest_time: Mapped[str] = mapped_column(default="08:00", server_default="08:00")
    list_sort: Mapped[str] = mapped_column(default="upcoming", server_default="upcoming")
    list_filter: Mapped[str | None] = mapped_column(default=None)
    adar_policy: Mapped[str] = mapped_column(default="adar_ii", server_default="adar_ii")
    feb29_policy: Mapped[str] = mapped_column(default="feb28", server_default="feb28")
    is_admin: Mapped[bool] = mapped_column(default=False, server_default="0")
    is_blocked: Mapped[bool] = mapped_column(default=False, server_default="0")
    bot_blocked_by_user: Mapped[bool] = mapped_column(default=False, server_default="0")
    onboarded: Mapped[bool] = mapped_column(default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    events: Mapped[list[Event]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reminder_rules: Mapped[list[ReminderRule]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    greeting_templates: Mapped[list[GreetingTemplate]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("language IN ('he','en')", name="lang_valid"),
        CheckConstraint("date_format IN ('DD/MM/YYYY','DD.MM.YYYY','YYYY-MM-DD')", name="df_valid"),
        CheckConstraint("time_format IN ('24h','12h')", name="tf_valid"),
        CheckConstraint(
            "list_sort IN ('upcoming','name','age','created')", name="list_sort_valid"
        ),
        CheckConstraint("adar_policy IN ('adar_i','adar_ii')", name="adar_policy_valid"),
        CheckConstraint("feb29_policy IN ('feb28','mar01')", name="feb29_policy_valid"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(default="birthday", server_default="birthday")
    custom_type_label: Mapped[str | None] = mapped_column(default=None)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str | None] = mapped_column(default=None)
    nickname: Mapped[str | None] = mapped_column(default=None)
    gender: Mapped[str | None] = mapped_column(default=None)
    relation: Mapped[str | None] = mapped_column(default=None)
    category: Mapped[str] = mapped_column(default="other", server_default="other")
    calendar_type: Mapped[str] = mapped_column(default="gregorian", server_default="gregorian")
    year: Mapped[int | None] = mapped_column(default=None)
    month: Mapped[int] = mapped_column()
    day: Mapped[int] = mapped_column()
    event_time: Mapped[str | None] = mapped_column(default=None)
    phone: Mapped[str | None] = mapped_column(default=None)
    telegram_username: Mapped[str | None] = mapped_column(default=None)
    photo_file_id: Mapped[str | None] = mapped_column(default=None)
    notes: Mapped[str | None] = mapped_column(default=None)
    next_occurrence: Mapped[date | None] = mapped_column(Date, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="events")
    reminder_rules: Mapped[list[ReminderRule]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[NotificationLog]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('birthday','anniversary','wedding','memorial','custom')",
            name="event_type_valid",
        ),
        CheckConstraint("calendar_type IN ('gregorian','hebrew')", name="calendar_type_valid"),
        CheckConstraint("month BETWEEN 1 AND 13", name="month_range"),
        CheckConstraint("day BETWEEN 1 AND 31", name="day_range"),
        CheckConstraint(
            "year IS NULL OR (year BETWEEN 1900 AND 2100) OR (year BETWEEN 5660 AND 5860)",
            name="year_range",
        ),
        CheckConstraint("gender IS NULL OR gender IN ('m','f','other')", name="gender_valid"),
        CheckConstraint(
            "category IN ('family','friends','work','clients','school','other')",
            name="category_valid",
        ),
        Index(
            "ix_events_user",
            "user_id",
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_events_next",
            "next_occurrence",
            sqlite_where=text("deleted_at IS NULL AND is_active = 1"),
        ),
        Index("ix_events_user_next", "user_id", "next_occurrence"),
        Index("ix_events_user_month", "user_id", "month"),
        Index("ix_events_name", "user_id", "first_name", "last_name"),
    )


class ReminderRule(Base):
    __tablename__ = "reminder_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), default=None
    )
    offset_days: Mapped[int | None] = mapped_column(default=None)
    offset_minutes: Mapped[int | None] = mapped_column(default=None)
    send_time: Mapped[str | None] = mapped_column(default=None)
    enabled: Mapped[bool] = mapped_column(default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="reminder_rules")
    event: Mapped[Event | None] = relationship(back_populates="reminder_rules")

    __table_args__ = (
        CheckConstraint(
            "(offset_days IS NOT NULL) <> (offset_minutes IS NOT NULL)",
            name="exactly_one_offset",
        ),
        Index("ix_rules_user", "user_id", "enabled"),
        Index("ix_rules_event", "event_id"),
    )


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("reminder_rules.id", ondelete="SET NULL"), default=None
    )
    occurrence_date: Mapped[date] = mapped_column(Date)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    status: Mapped[str] = mapped_column(default="pending", server_default="pending")
    error: Mapped[str | None] = mapped_column(default=None)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")

    user: Mapped[User] = relationship()
    event: Mapped[Event] = relationship(back_populates="notifications")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','sent','failed','skipped')", name="notif_status_valid"
        ),
        UniqueConstraint("event_id", "rule_id", "occurrence_date", name="uq_notif"),
        Index("ix_notif_sched", "status", "scheduled_at"),
    )


class GreetingTemplate(Base):
    __tablename__ = "greeting_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    event_type: Mapped[str] = mapped_column()
    tone: Mapped[str] = mapped_column()
    gender: Mapped[str | None] = mapped_column(default=None)
    language: Mapped[str] = mapped_column()
    body: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True, server_default="1")

    user: Mapped[User | None] = relationship(back_populates="greeting_templates")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('birthday','anniversary','wedding','memorial','custom')",
            name="tpl_event_type_valid",
        ),
        CheckConstraint("tone IN ('warm','funny','formal','short')", name="tpl_tone_valid"),
        CheckConstraint("gender IS NULL OR gender IN ('m','f')", name="tpl_gender_valid"),
        CheckConstraint("language IN ('he','en')", name="tpl_lang_valid"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column()
    entity: Mapped[str] = mapped_column()
    entity_id: Mapped[int | None] = mapped_column(default=None)
    payload: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_user_time", "user_id", "created_at"),)


class Backup(Base):
    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    kind: Mapped[str] = mapped_column()
    format: Mapped[str] = mapped_column()
    path: Mapped[str] = mapped_column()
    size_bytes: Mapped[int] = mapped_column(default=0, server_default="0")
    events_count: Mapped[int] = mapped_column(default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("kind IN ('auto','manual','export')", name="backup_kind_valid"),
        CheckConstraint("format IN ('db','json','csv','xlsx')", name="backup_format_valid"),
    )


class AppMeta(Base):
    __tablename__ = "app_meta"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str | None] = mapped_column(default=None)


__all__ = [
    "AppMeta",
    "AuditLog",
    "Backup",
    "Event",
    "GreetingTemplate",
    "NotificationLog",
    "ReminderRule",
    "User",
]
