from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    WEDDING = "wedding"
    MEMORIAL = "memorial"
    CUSTOM = "custom"


class CalendarType(StrEnum):
    GREGORIAN = "gregorian"
    HEBREW = "hebrew"


class Category(StrEnum):
    FAMILY = "family"
    FRIENDS = "friends"
    WORK = "work"
    CLIENTS = "clients"
    SCHOOL = "school"
    OTHER = "other"


class Gender(StrEnum):
    MALE = "m"
    FEMALE = "f"
    OTHER = "other"


class Tone(StrEnum):
    WARM = "warm"
    FUNNY = "funny"
    FORMAL = "formal"
    SHORT = "short"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class Language(StrEnum):
    HE = "he"
    EN = "en"


class DateFormat(StrEnum):
    DMY_SLASH = "DD/MM/YYYY"
    DMY_DOT = "DD.MM.YYYY"
    ISO = "YYYY-MM-DD"


class TimeFormat(StrEnum):
    H24 = "24h"
    H12 = "12h"


class ListSort(StrEnum):
    UPCOMING = "upcoming"
    NAME = "name"
    AGE = "age"
    CREATED = "created"


class ListView(StrEnum):
    UPCOMING = "upcoming"
    ALL = "all"
    MUTED = "muted"
    TRASH = "trash"


class AdarPolicy(StrEnum):
    ADAR_I = "adar_i"
    ADAR_II = "adar_ii"


class Feb29Policy(StrEnum):
    FEB28 = "feb28"
    MAR01 = "mar01"


class BackupKind(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"
    EXPORT = "export"


class BackupFormat(StrEnum):
    DB = "db"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


class AuditAction(StrEnum):
    START = "start"
    EVENT_CREATE = "event_create"
    EVENT_UPDATE = "event_update"
    EVENT_DELETE = "event_delete"
    EVENT_RESTORE = "event_restore"
    RULE_CREATE = "rule_create"
    RULE_DELETE = "rule_delete"
    SETTINGS_UPDATE = "settings_update"
    EXPORT = "export"
    IMPORT = "import"
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_FAILED = "notification_failed"
    ADMIN_BROADCAST = "admin_broadcast"
    USER_BLOCKED = "user_blocked"
    ERROR = "error"


# Field length limits (chapter 27)
NAME_MAX_LEN = 64
NICKNAME_MAX_LEN = 32
NOTES_MAX_LEN = 500
PHONE_MAX_LEN = 20
RELATION_MAX_LEN = 32
CUSTOM_TYPE_LABEL_MAX_LEN = 32

# Domain limits
MIN_YEAR_GREGORIAN = 1900
MAX_YEAR_GREGORIAN = 2100
MIN_YEAR_HEBREW = 5660
MAX_YEAR_HEBREW = 5860
MAX_REMINDER_RULES_GLOBAL = 5
MAX_REMINDER_RULES_PER_EVENT = 5
MAX_GREETING_TEMPLATES_PER_USER = 20
SOFT_DELETE_RETENTION_DAYS = 30

# Offsets available in the quick reminder-add flow (chapter 15, S11)
REMINDER_OFFSET_CHOICES = (0, 1, 2, 3, 7, 14, 30)

HEBREW_MONTH_NAMES = (
    "ניסן",
    "אייר",
    "סיוון",
    "תמוז",
    "אב",
    "אלול",
    "תשרי",
    "חשוון",
    "כסלו",
    "טבת",
    "שבט",
    "אדר",
    "אדר ב׳",
)
