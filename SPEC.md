# אפיון מערכת מלא — בוט "בלי פאדיחות" (Birthly)

> **מסמך זה הוא ה‑Source of Truth היחיד של הפרויקט.**
> ממנו נבנה הכל: מבנה קבצים, סכימת DB, כל מסך, כל כפתור, כל callback, וכל כלל התנהגות.
> סוכן AI שמפתח את הפרויקט לא אמור להמציא שום דבר שלא כתוב כאן. אם משהו חסר — ראה פרק 36 (שאלות פתוחות), שם רשומה ברירת מחדל מחייבת לכל מקרה.
>
> **גרסה:** 1.0 · **תאריך:** יולי 2026 · **סטטוס:** מאושר לפיתוח

**החלטות מוצר שנסגרו:** Python + aiogram 3 · שם תצוגה "בלי פאדיחות" (שם טכני `birthly`) · תזכורת לפי הלוח שנבחר בלבד · פריסה systemd + venv (בלי Docker) · עברית ברירת מחדל עם החלפת שפה · תמיכה בלוח עברי · בלי ייבוא אנשי קשר · בלי שליחת ברכות אוטומטית (רק תבניות) · בלי פאנל web · אירועים גנריים עם סיווג · בלי Premium · בלי ארכיטקטורת Plugins · סקייל קטן.

---

## תוכן עניינים

1. [Project Overview](#1-project-overview)
2. [Vision / Goals / Non‑Goals](#2-vision--goals--non-goals)
3. [קהל יעד ופרסונות](#3-קהל-יעד-ופרסונות)
4. [Technical Stack](#4-technical-stack)
5. [Architecture](#5-architecture)
6. [Folder Structure](#6-folder-structure)
7. [Configuration](#7-configuration)
8. [Database Design](#8-database-design)
9. [Domain Model & Core Logic](#9-domain-model--core-logic)
10. [Hebrew Calendar Support](#10-hebrew-calendar-support)
11. [User Flow](#11-user-flow)
12. [Commands](#12-commands)
13. [Callback IDs](#13-callback-ids)
14. [FSM States](#14-fsm-states)
15. [Screen Specifications](#15-screen-specifications)
16. [Messages & Copy](#16-messages--copy)
17. [Scheduler](#17-scheduler)
18. [Reminder Engine](#18-reminder-engine)
19. [Localization (i18n)](#19-localization-i18n)
20. [Settings](#20-settings)
21. [Statistics](#21-statistics)
22. [Templates (ברכות)](#22-templates-ברכות)
23. [Backup System](#23-backup-system)
24. [Admin](#24-admin)
25. [Logging](#25-logging)
26. [Error Handling](#26-error-handling)
27. [Security](#27-security)
28. [Coding Standards](#28-coding-standards)
29. [UX Rules](#29-ux-rules)
30. [Design Rules](#30-design-rules)
31. [Performance](#31-performance)
32. [Testing](#32-testing)
33. [Deployment](#33-deployment)
34. [Future Ideas](#34-future-ideas)
35. [Milestones לסוכן המפתח](#35-milestones-לסוכן-המפתח)
36. [שאלות פתוחות](#36-שאלות-פתוחות)
37. [Verification](#37-verification)

---

## 1. Project Overview

**בלי פאדיחות** הוא בוט טלגרם אישי לניהול תאריכים חוזרים — ימי הולדת בראש ובראשונה, ובנוסף ימי נישואין, ימי חתונה, אזכרות ואירועים מותאמים אישית — ושליחת תזכורות חכמות מראש, בלוח הגרגוריאני או העברי.

המשתמש מוסיף אדם + תאריך בשלושה צעדים, והבוט דואג לשאר: מחשב את המופע הבא, שולח תזכורות בשעה שהמשתמש בחר, מציג כרטיס אישי עם גיל וספירה לאחור, ומציע תבניות ברכה מוכנות להעתקה.

**הגדרה בשורה אחת:** פשוט יותר מלוח שנה, מהיר יותר מאפליקציה, חי כולו בתוך טלגרם.

---

## 2. Vision / Goals / Non‑Goals

### Vision
שאף אחד לא ישכח יום הולדת של מישהו שחשוב לו — בלי להתקין כלום, בלי הרשמה, בלי ללמוד ממשק.

### Goals (V1)
| # | מטרה | מדד הצלחה |
|---|------|-----------|
| G1 | הוספת אירוע ראשון תוך פחות מ‑30 שניות | **2 מסכים** מ‑`[➕ הוסף]` עד "נשמר" (פרק 11.1) |
| G2 | תזכורות שמגיעות בזמן, פעם אחת בדיוק | 0 כפילויות, 0 החמצות מעל grace window |
| G3 | תמיכה מלאה ולא־חלקית בלוח העברי | כולל ל׳ חשוון, ל׳ כסלו, אדר א׳/ב׳ |
| G4 | עברית תקינה ונקייה, בלי "תרגומית" | כל מחרוזת עוברת בדיקה ידנית |
| G5 | אפס אובדן נתונים | גיבוי יומי אוטומטי + ייצוא ידני |
| G6 | ניווט בלי מבוי סתום | לכל מסך יש חזרה/בית |

### Non‑Goals (במפורש מחוץ ל‑V1)
- ❌ שליחת ברכות אוטומטית לאדם עצמו (רק תבניות להעתקה)
- ❌ ייבוא מאנשי קשר של הטלפון / Google Contacts
- ❌ פאנל ניהול Web
- ❌ מנוי Premium / תשלומים / הרשאות מדורגות
- ❌ ארכיטקטורת Plugins דינמית
- ❌ ריבוי משתמשים על אותו אירוע / שיתוף רשימות
- ❌ Inline mode, Web App, Mini App
- ❌ סנכרון Google Calendar (Future)

---

## 3. קהל יעד ופרסונות

| פרסונה | תיאור | צורך מרכזי |
|--------|-------|------------|
| **דני, 34, מרובה־קשרים** | ~60 אנשים ברשימה: משפחה, חברים, לקוחות | לא לפספס לקוח; סינון לפי קטגוריה |
| **מיכל, 28, דתית** | מציינת ימי הולדת בתאריך עברי | תמיכה אמיתית בלוח העברי |
| **אבי, 55, לא טכנולוגי** | רוצה רק שיזכירו לו | ממשק כפתורים בלבד, בלי הקלדת פקודות |

**מכנה משותף:** אפס ידע טכני, אפס סבלנות, שימוש מהנייד.

---

## 4. Technical Stack

| רכיב | בחירה | גרסה | למה |
|------|-------|------|-----|
| שפה | Python | 3.12+ | pyluach, זמינות ספריות |
| Bot framework | **aiogram** | 3.x (latest) | async, Router, FSM מובנה, middlewares |
| DB | **SQLite** | 3.40+ | סקייל קטן, קובץ אחד, גיבוי טריוויאלי |
| ORM | **SQLAlchemy** | 2.0 async | מעבר ל‑Postgres בעתיד בלי כתיבה מחדש |
| DB driver | aiosqlite | latest | |
| Migrations | **Alembic** | latest | |
| Scheduler | **APScheduler** | 3.x (`AsyncIOScheduler`) | cron jobs בתוך אותו event loop |
| לוח עברי | **pyluach** | latest | המרות + שנים מעוברות + אורכי חודשים |
| Config | pydantic-settings | 2.x | ולידציה של `.env` בעליית התהליך |
| Timezones | zoneinfo (stdlib) | — | |
| Excel export | openpyxl | latest | |
| Logging | structlog + stdlib | latest | JSON לקובץ, טקסט ל‑journald |
| Tests | pytest, pytest‑asyncio | latest | |
| Lint/Format | ruff | latest | lint + format בכלי אחד |
| Types | mypy (strict על `core/` ו‑`services/`) | latest | |

**`requirements.txt`:**
```
aiogram>=3.15
SQLAlchemy[asyncio]>=2.0
aiosqlite>=0.20
alembic>=1.13
APScheduler>=3.10,<4
pyluach>=2.2
pydantic-settings>=2.5
openpyxl>=3.1
structlog>=24.0
python-dateutil>=2.9
```
**`requirements-dev.txt`:** `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`, `freezegun`

> **הערה לסוכן:** אין להוסיף תלויות מעבר לרשימה בלי סיבה מתועדת. אין Docker, אין Redis, אין Celery.

---

## 5. Architecture

### שכבות (הפרדה נוקשה — הפרה = באג)

```
┌─────────────────────────────────────────────────────┐
│  Telegram  ←→  aiogram Dispatcher (long polling)    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  MIDDLEWARES (סדר קבוע)                              │
│  1. LoggingMiddleware   (correlation_id = update_id) │
│  2. DbSessionMiddleware (session per update)         │
│  3. UserMiddleware      (get_or_create + is_blocked) │
│  4. ThrottlingMiddleware(rate limit per user)        │
│  5. I18nMiddleware      (מזריק `_` לפי user.language)│
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  HANDLERS  — רק ניתוב, ולידציה בסיסית ורינדור.        │
│              אסור SQL. אסור לוגיקה עסקית.             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  SERVICES  — כל הלוגיקה העסקית. לא מכיר aiogram.      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  REPOSITORIES — כל ה‑SQL. כל שאילתה מסוננת ב‑user_id  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  DB (SQLite, WAL)                                    │
└─────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ SCHEDULER (APScheduler) → Services → Bot API │
  │ רץ באותו process, אותו event loop             │
  └──────────────────────────────────────────────┘

  CORE — פונקציות טהורות (dates, hebcal, formatting, validators).
         אין להן state, אין DB, אין I/O. 100% מכוסות בטסטים.
```

### כללי תלות
- `handlers` → `services` → `repositories` → `db.models`
- `core` — לא תלוי באף שכבה. כולם יכולים לתלות בו.
- `scheduler.jobs` → `services` בלבד (לעולם לא repositories ישירות).
- אסור import הפוך (service שמייבא handler) — ruff יאכוף.

### Concurrency
תהליך יחיד, event loop יחיד. Long polling (`bot.delete_webhook(drop_pending_updates=True)` בעלייה). אין multi‑worker — SQLite + APScheduler לא מתאימים לזה, ולא צריך בסקייל הזה.

---

## 6. Folder Structure

```
Birthly/
├── .env                          # לא ב‑git
├── .env.example
├── .gitignore
├── README.md
├── SPEC.md                        # המסמך הזה — Source of Truth
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml                 # ruff + mypy + pytest config
├── alembic.ini
├── Makefile                       # run / test / lint / migrate / backup
│
├── deploy/
│   ├── birthly.service            # systemd unit
│   ├── install.sh                 # התקנה מלאה על שרת נקי
│   ├── update.sh                  # git pull + migrate + restart
│   └── logrotate.birthly
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
│
├── locales/
│   ├── he.json                    # ברירת מחדל — מקור האמת
│   └── en.json
│
├── data/                          # gitignored לחלוטין
│   ├── birthly.db
│   ├── backups/
│   └── logs/
│
├── tests/
│   ├── conftest.py
│   ├── test_dates_gregorian.py
│   ├── test_dates_hebrew.py
│   ├── test_reminder_engine.py
│   ├── test_event_service.py
│   ├── test_backup_service.py
│   ├── test_validators.py
│   ├── test_formatting.py
│   └── test_handlers_smoke.py
│
└── app/
    ├── __init__.py
    ├── main.py                    # entrypoint: bootstrap + polling
    ├── config.py                  # Settings (pydantic-settings)
    ├── constants.py               # Enums, קטגוריות, אימוג'ים, מגבלות
    │
    ├── core/                      # פונקציות טהורות בלבד
    │   ├── dates.py               # next_occurrence, age, days_until
    │   ├── hebcal.py              # עטיפה ל‑pyluach + edge cases
    │   ├── formatting.py          # פורמט תאריך/שעה/גיל/שם, RTL
    │   ├── validators.py          # ולידציה של כל קלט משתמש
    │   └── text.py                # escape HTML, קיצור, pluralization
    │
    ├── db/
    │   ├── base.py                # DeclarativeBase, naming convention
    │   ├── session.py             # engine, sessionmaker, PRAGMA setup
    │   ├── models.py              # כל המודלים
    │   └── repositories/
    │       ├── base.py            # BaseRepository (user-scoped)
    │       ├── users.py
    │       ├── events.py
    │       ├── reminders.py
    │       ├── notifications.py
    │       ├── templates.py
    │       └── audit.py
    │
    ├── services/
    │   ├── user_service.py
    │   ├── event_service.py
    │   ├── reminder_service.py    # ← הלב של המערכת
    │   ├── stats_service.py
    │   ├── template_service.py
    │   ├── backup_service.py
    │   ├── notify_service.py      # שליחה בפועל + rate limit + retry
    │   └── admin_service.py
    │
    ├── handlers/
    │   ├── __init__.py            # register_all_routers(dp)
    │   ├── start.py
    │   ├── menu.py
    │   ├── event_add.py
    │   ├── event_list.py
    │   ├── event_card.py
    │   ├── event_edit.py
    │   ├── search.py
    │   ├── reminders.py
    │   ├── settings.py
    │   ├── stats.py
    │   ├── templates.py
    │   ├── backup.py
    │   ├── admin.py
    │   ├── help.py
    │   └── fallback.py            # unknown input — תמיד אחרון
    │
    ├── keyboards/
    │   ├── common.py              # back/home/confirm/cancel
    │   ├── menu.py
    │   ├── events.py
    │   ├── settings.py
    │   ├── reminders.py
    │   ├── admin.py
    │   └── pagination.py          # builder גנרי לדפדוף
    │
    ├── callbacks/
    │   └── factories.py           # כל ה‑CallbackData factories
    │
    ├── states/
    │   └── forms.py               # כל ה‑StatesGroup
    │
    ├── middlewares/
    │   ├── db.py
    │   ├── user.py
    │   ├── i18n.py
    │   ├── throttling.py
    │   └── logging.py
    │
    ├── scheduler/
    │   ├── scheduler.py           # build_scheduler()
    │   └── jobs.py                # כל ה‑jobs
    │
    ├── i18n/
    │   └── translator.py          # load locales, t(key, lang, **kw)
    │
    └── utils/
        ├── logger.py              # setup_logging()
        └── ratelimit.py           # AsyncRateLimiter (טוקן באקט)
```

---

## 7. Configuration

### `.env.example`
```env
# ── Telegram ───────────────────────────────────
BOT_TOKEN=123456:ABC-DEF...
BOT_USERNAME=Birthday_ILBOT
ADMIN_IDS=123456789,987654321

# ── Database ───────────────────────────────────
DB_PATH=data/birthly.db

# ── Defaults ───────────────────────────────────
DEFAULT_LANGUAGE=he
DEFAULT_TIMEZONE=Asia/Jerusalem
DEFAULT_NOTIFY_TIME=09:00
DEFAULT_DATE_FORMAT=DD/MM/YYYY
DEFAULT_TIME_FORMAT=24h

# ── Scheduler ──────────────────────────────────
SCHEDULER_TICK_SECONDS=60
REMINDER_GRACE_HOURS=6          # חלון השלמה אחרי downtime
MAX_UPCOMING_DAYS=45            # אופק חישוב מופעים

# ── Limits ─────────────────────────────────────
MAX_EVENTS_PER_USER=1000
RATE_LIMIT_MESSAGES=20          # לדקה
RATE_LIMIT_CALLBACKS=40         # לדקה
BROADCAST_RATE_PER_SEC=20
PAGE_SIZE=8

# ── Backup ─────────────────────────────────────
AUTO_BACKUP_ENABLED=true
AUTO_BACKUP_TIME=03:30
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=data/backups

# ── Logging ────────────────────────────────────
LOG_LEVEL=INFO
LOG_DIR=data/logs
LOG_JSON=true
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# ── Misc ───────────────────────────────────────
ENV=production                  # development | production
REPORT_ERRORS_TO_ADMIN=true
```

### כללים
- `app/config.py` טוען עם pydantic-settings ומפיל את התהליך עם הודעה ברורה אם חסר שדה חובה (`BOT_TOKEN`, `ADMIN_IDS`).
- `Settings` הוא singleton (`settings = Settings()`), מיובא ישירות — לא מועבר בפרמטרים.
- אין ערכי קסם בקוד. כל מספר/מחרוזת קבועה יושבים ב‑`config.py` או `constants.py`.

---

## 8. Database Design

### ERD

```
users 1──∞ events 1──∞ reminder_rules
  │            │              │
  │            └──∞ notifications_log ──┘
  ├──∞ reminder_rules (event_id NULL = כלל גלובלי)
  ├──∞ greeting_templates
  └──∞ audit_logs
```

### `users`
| עמודה | טיפוס | ברירת מחדל | הערות |
|-------|-------|------------|-------|
| `id` | INTEGER PK | — | telegram user_id (לא AUTOINCREMENT) |
| `username` | TEXT NULL | | |
| `first_name` | TEXT | | מטלגרם |
| `last_name` | TEXT NULL | | |
| `language` | TEXT | `'he'` | `he` \| `en` |
| `timezone` | TEXT | `'Asia/Jerusalem'` | IANA |
| `date_format` | TEXT | `'DD/MM/YYYY'` | \|`DD.MM.YYYY`\|`YYYY-MM-DD` |
| `time_format` | TEXT | `'24h'` | `24h` \| `12h` |
| `default_notify_time` | TEXT | `'09:00'` | HH:MM מקומי |
| `notifications_enabled` | BOOL | `1` | כיבוי גורף |
| `silent_notifications` | BOOL | `0` | `disable_notification=True` |
| `show_hebrew_date` | BOOL | `1` | הצגת התאריך העברי המקביל בכרטיס |
| `daily_digest_enabled` | BOOL | `0` | סיכום יומי |
| `digest_time` | TEXT | `'08:00'` | |
| `list_sort` | TEXT | `'upcoming'` | `upcoming`\|`name`\|`age`\|`created` |
| `list_filter` | TEXT NULL | NULL | קטגוריה / סוג אירוע |
| `is_admin` | BOOL | `0` | מסונכרן מ‑`ADMIN_IDS` בעלייה |
| `is_blocked` | BOOL | `0` | חסום ע"י אדמין |
| `bot_blocked_by_user` | BOOL | `0` | המשתמש חסם את הבוט |
| `onboarded` | BOOL | `0` | סיים אשף פתיחה |
| `created_at` / `updated_at` / `last_seen_at` | DATETIME | now | UTC |

### `events` — הישות המרכזית
| עמודה | טיפוס | הערות |
|-------|-------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `user_id` | INTEGER FK→users ON DELETE CASCADE | **מסונן בכל שאילתה** |
| `event_type` | TEXT | `birthday`\|`anniversary`\|`wedding`\|`memorial`\|`custom` |
| `custom_type_label` | TEXT NULL | כשה‑type הוא `custom` |
| `first_name` | TEXT NOT NULL | 1–64 |
| `last_name` | TEXT NULL | 0–64 |
| `nickname` | TEXT NULL | 0–32 |
| `gender` | TEXT NULL | `m`\|`f`\|`other` — משפיע על ניסוח ההודעה |
| `relation` | TEXT NULL | אבא/אמא/אח/בן זוג... 0–32 |
| `category` | TEXT | `family`\|`friends`\|`work`\|`clients`\|`school`\|`other` |
| `calendar_type` | TEXT | `gregorian` \| `hebrew` |
| `year` | INTEGER NULL | NULL = שנה לא ידועה → בלי גיל |
| `month` | INTEGER NOT NULL | 1–12 גרגוריאני, 1–13 עברי |
| `day` | INTEGER NOT NULL | 1–31 / 1–30 |
| `event_time` | TEXT NULL | HH:MM — "שעת לידה", מאפשר תזכורת יחסית |
| `phone` | TEXT NULL | E.164 או פורמט ישראלי |
| `telegram_username` | TEXT NULL | בלי `@` בשמירה |
| `photo_file_id` | TEXT NULL | **file_id של טלגרם בלבד — לא שומרים קבצים בדיסק** |
| `notes` | TEXT NULL | 0–500 |
| `next_occurrence` | DATE NULL | תאריך גרגוריאני מחושב (cache) |
| `is_active` | BOOL default 1 | כיבוי תזכורות לאירוע בודד |
| `deleted_at` | DATETIME NULL | **soft delete** — 30 יום ואז purge |
| `created_at` / `updated_at` | DATETIME | |

**אילוצים:**
```sql
CHECK (event_type IN ('birthday','anniversary','wedding','memorial','custom'))
CHECK (calendar_type IN ('gregorian','hebrew'))
CHECK (month BETWEEN 1 AND 13)
CHECK (day BETWEEN 1 AND 31)
CHECK (year IS NULL OR year BETWEEN 1900 AND 2100)   -- עברי: 5660-5860
```

### `reminder_rules`
| עמודה | טיפוס | הערות |
|-------|-------|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | |
| `event_id` | INTEGER FK NULL | **NULL = כלל גלובלי** לכל האירועים של המשתמש |
| `offset_days` | INTEGER NULL | 0=ביום עצמו, 1, 2, 3, 7, 14, 30 |
| `offset_minutes` | INTEGER NULL | תזכורת יחסית לשעת האירוע (למשל 120 = שעתיים לפני). תקף **רק** אם `events.event_time` קיים |
| `send_time` | TEXT NULL | HH:MM; NULL → `users.default_notify_time` |
| `enabled` | BOOL default 1 | |
| `created_at` | DATETIME | |

**אילוץ:** `CHECK ((offset_days IS NOT NULL) <> (offset_minutes IS NOT NULL))` — בדיוק אחד מהשניים.
**ברירת מחדל למשתמש חדש:** שני כללים גלובליים — `offset_days=1` ו‑`offset_days=0`, שניהם ב‑`send_time=NULL`.
**מקסימום:** 5 כללים גלובליים, 5 לכל אירוע.

### `notifications_log` — מנוע האידמפוטנטיות
| עמודה | טיפוס | הערות |
|-------|-------|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | |
| `event_id` | INTEGER FK | |
| `rule_id` | INTEGER FK NULL | NULL אם הכלל נמחק |
| `occurrence_date` | DATE | התאריך הגרגוריאני של המופע |
| `scheduled_at` | DATETIME | UTC — מתי היה אמור להישלח |
| `sent_at` | DATETIME NULL | |
| `status` | TEXT | `pending`\|`sent`\|`failed`\|`skipped` |
| `error` | TEXT NULL | |
| `attempts` | INTEGER default 0 | |

```sql
CREATE UNIQUE INDEX uq_notif ON notifications_log(event_id, rule_id, occurrence_date);
```
> זה המפתח למניעת כפילויות: גם אם ה‑tick רץ פעמיים או שהתהליך קרס באמצע, ה‑UNIQUE חוסם שליחה כפולה.

### `greeting_templates`
| עמודה | טיפוס | הערות |
|-------|-------|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK NULL | NULL = תבנית מערכת (seed) |
| `event_type` | TEXT | לאיזה סוג אירוע |
| `tone` | TEXT | `warm`\|`funny`\|`formal`\|`short` |
| `gender` | TEXT NULL | `m`\|`f`\|NULL (ניטרלי) |
| `language` | TEXT | `he`\|`en` |
| `body` | TEXT | תומך placeholders: `{name}`, `{nickname}`, `{age}`, `{relation}` |
| `is_active` | BOOL | |

### `audit_logs`
`id`, `user_id`, `action` (TEXT), `entity` (TEXT), `entity_id` (INT NULL), `payload` (JSON TEXT), `created_at`.
`action` מתוך: `start`, `event_create`, `event_update`, `event_delete`, `event_restore`, `rule_create`, `rule_delete`, `settings_update`, `export`, `import`, `notification_sent`, `notification_failed`, `admin_broadcast`, `user_blocked`, `error`.

### `backups`
`id`, `user_id` (NULL=גיבוי מערכת), `kind` (`auto`\|`manual`\|`export`), `format` (`db`\|`json`\|`csv`\|`xlsx`), `path`, `size_bytes`, `events_count`, `created_at`.

### `app_meta`
`key` TEXT PK, `value` TEXT — עבור `schema_version`, `last_tick_at`, `bot_started_at`.

### Indexes
```sql
CREATE INDEX ix_events_user            ON events(user_id) WHERE deleted_at IS NULL;
CREATE INDEX ix_events_next            ON events(next_occurrence) WHERE deleted_at IS NULL AND is_active = 1;
CREATE INDEX ix_events_user_next       ON events(user_id, next_occurrence);
CREATE INDEX ix_events_user_month      ON events(user_id, month);
CREATE INDEX ix_events_name            ON events(user_id, first_name, last_name);
CREATE INDEX ix_rules_user             ON reminder_rules(user_id, enabled);
CREATE INDEX ix_rules_event            ON reminder_rules(event_id);
CREATE INDEX ix_notif_sched            ON notifications_log(status, scheduled_at);
CREATE INDEX ix_audit_user_time        ON audit_logs(user_id, created_at);
```

### PRAGMAs (ב‑`db/session.py`, על כל חיבור)
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

---

## 9. Domain Model & Core Logic

### `core/dates.py` — חתימות מדויקות

```python
def next_occurrence(
    calendar_type: str, year: int | None, month: int, day: int,
    today: date, adar_policy: str = "adar_ii", feb29_policy: str = "feb28",
) -> date:
    """מחזיר את התאריך הגרגוריאני של המופע הבא. אם המופע היום — מחזיר היום."""

def days_until(target: date, today: date) -> int: ...

def age_at(
    calendar_type: str, year: int | None, month: int, day: int, on: date
) -> int | None:
    """גיל במופע. None אם השנה לא ידועה. עברי → הפרש שנים עבריות."""

def upcoming_between(events, start: date, end: date) -> list[tuple[Event, date]]: ...
```

### חוקי חישוב

**גרגוריאני:**
1. נסה `date(today.year, month, day)`.
2. אם `>= today` → זו התשובה. אחרת `date(today.year+1, month, day)`.
3. 29/02 בשנה לא מעוברת → לפי `feb29_policy`: `feb28` (ברירת מחדל) או `mar01`.

**עברי:** ראה פרק 10.

**גיל:**
- גרגוריאני: `occurrence.year - year` (כי המופע כבר "אחרי" יום ההולדת).
- עברי: `hebrew_year_of(occurrence) - hebrew_birth_year`.
- `year IS NULL` → מציגים "🎂 יום הולדת" בלי מספר, ובכל מקום שמופיע גיל מציגים `—`.
- `event_type = memorial` → מציגים "שנה X" ולא "גיל".

**אזורי זמן:** כל ה‑DB ב‑**UTC**. כל חישוב "היום" נעשה ב‑`users.timezone`:
```python
user_today = datetime.now(ZoneInfo(user.timezone)).date()
```
מעבר שעון קיץ: תזכורת ב‑09:00 מקומי תמיד תישלח ב‑09:00 מקומי, כי ההמרה ל‑UTC נעשית מחדש בכל tick, לא נשמרת מראש.

---

## 10. Hebrew Calendar Support

**החלטה:** לכל אירוע יש `calendar_type` יחיד. התזכורת יוצאת **רק** לפי הלוח שנבחר. בכרטיס האירוע מוצגים שני התאריכים לנוחות (אם `users.show_hebrew_date=1`).

### מיפוי חודשים (pyluach)
| # | חודש | # | חודש |
|---|------|---|------|
| 1 | ניסן | 8 | חשוון |
| 2 | אייר | 9 | כסלו |
| 3 | סיוון | 10 | טבת |
| 4 | תמוז | 11 | שבט |
| 5 | אב | 12 | אדר / **אדר א׳** (בשנה מעוברת) |
| 6 | אלול | 13 | **אדר ב׳** (רק בשנה מעוברת) |
| 7 | תשרי | | |

> **חובה:** לכתוב טסט שמאמת את המיפוי מול הגרסה המותקנת של pyluach לפני שבונים עליו לוגיקה.

### Edge cases — התנהגות מחייבת

| מקרה | התנהגות |
|------|---------|
| **ל׳ חשוון** (8/30) בשנה שחשוון בה חסר | נופל ל‑**כ״ט חשוון** (היום האחרון של החודש) |
| **ל׳ כסלו** (9/30) בשנה שכסלו בה חסר | נופל ל‑**כ״ט כסלו** |
| נולד ב**אדר** (שנה פשוטה) → שנה מעוברת | **אדר ב׳** (ברירת מחדל, `adar_policy=adar_ii`); ניתן להגדיר `adar_i` |
| נולד ב**אדר א׳** → שנה פשוטה | אדר |
| נולד ב**אדר ב׳** → שנה פשוטה | אדר |
| **ל׳ אדר א׳** → שנה פשוטה | נופל לכ״ט אדר |

**כלל אב:** אם היום המבוקש לא קיים בחודש היעד — יורדים ליום האחרון הקיים באותו חודש. **לעולם לא גולשים לחודש הבא** (מונע קפיצה של תזכורת לחודש שגוי).

### `core/hebcal.py` — API
```python
def to_hebrew(d: date) -> tuple[int, int, int]                 # (year, month, day)
def to_gregorian(h_year: int, h_month: int, h_day: int) -> date
def is_leap_year(h_year: int) -> bool
def month_length(h_year: int, h_month: int) -> int
def resolve_month(h_year: int, src_month: int, policy: str) -> int   # טיפול באדר
def format_hebrew_date(h_year, h_month, h_day, with_year=True) -> str
    # → "י״ד בניסן תשפ״ו"  (גימטריה מלאה, לא "14 ניסן")
def hebrew_year_gematria(y: int) -> str                        # 5786 → "תשפ״ו"
```

### הזנת תאריך עברי בממשק
המשתמש **לא מקליד** תאריך עברי כטקסט חופשי. הזרימה:
1. בורר חודש (13 כפתורים בגריד, אדר ב׳ מוצג רק אם רלוונטי).
2. בורר יום (גריד, מוגבל לאורך החודש בפועל).
3. שנה: כפתור "לא יודע" או הקלדה — מקבל גם `5750` וגם `1990` (מזהה אוטומטית לפי הטווח וממיר).

### תצוגה
```
🎂 יום ההולדת של שרה
📅 י״ד באדר תשפ״ו  ·  03/03/2026
```

---

## 11. User Flow

### 11.1 חוזה הפשטות — הכלל שגובר על הכל

> זה הכלל החשוב ביותר בכל המסמך. כל התנגשות בינו לבין פרט אחר — הוא מנצח.

**רק שני שדות הם חובה בכל המערכת: `first_name` ו‑(`month` + `day`).**
כל דבר אחר — שנה, קטגוריה, סוג אירוע, מין, קשר, טלפון, תמונה, הערות, שעה, לוח, כינוי — הוא אופציונלי, ולכל שאלה עליו יש דרך יציאה בלחיצה אחת.

| כלל | מימוש |
|-----|-------|
| **הוספה = 2 מסכים** | שם → תאריך → נשמר. זהו. |
| **הבוט לא שואל על תזכורות בהוספה** | משתמש חדש מקבל אוטומטית "יום לפני" + "ביום עצמו" ב‑09:00. אפשר לשנות אחר כך, אף פעם לא חייבים. |
| **כל שאלה שאינה שם/תאריך — עם `דלג ←`** | וכפתור הדילוג הוא **ברירת המחדל הוויזואלית**: הוא רחב, בשורה נפרדת, ולא מוסתר בפינה. |
| **דילוג לא עולה כלום** | דילגת על השנה? הכרטיס פשוט לא מציג גיל. שום אזהרה, שום "שים לב שחסר", שום כוכבית אדומה. |
| **אין שדה חובה מוסווה** | אסור מסך שאי אפשר להתקדם ממנו בלי למלא, חוץ משם ותאריך. |
| **פרטים נוספים — רק אחרי השמירה** | אף פעם לא לפני. האירוע כבר בטוח ב‑DB כשמציעים להעשיר אותו. |
| **הוספת תזכורת = 1–2 לחיצות** | בחירת מרווח → נשמר בשעת ברירת המחדל. בחירת שעה היא צעד אופציונלי, לא שלב בזרימה. |

### Onboarding (משתמש חדש)
```
/start
  → הודעת ברוכים הבאים (2 שורות, לא נאום)  +  [דלג על הכל ←]
  → "באיזו שפה?"  [🇮🇱 עברית] [🇬🇧 English]
  → "מה אזור הזמן?" [ישראל 🇮🇱] [אחר...]     ← ישראל = ברירת מחדל בלחיצה אחת
  → "מתי לשלוח תזכורות?" [09:00] [12:00] [18:00] [שעה אחרת]
  → "בוא נוסיף את הראשון 🎂"  → זרימת הוספה
  → onboarded = 1
```
**כללים:** לא יותר מ‑4 מסכים · `דלג ←` בכל שלב · `[דלג על הכל ←]` במסך הראשון קופץ ישר לזרימת ההוספה · דילוג משאיר את ברירות המחדל מפרק 20 · האונבורדינג לא חוזר לעולם.

### Happy Path — הוספת אירוע (2 מסכים)
```
[➕ הוסף] → "מה השם?" (טקסט)
         → "מתי?"  הקלדה חופשית: "15/03/1990" / "15.3.90" / "15 במרץ"
                   + [✡️ תאריך עברי]  ← מסלול צדדי, למי שצריך
                   + [🤷 לא יודע את השנה]
         → "מעולה! נוסף ✅"  + כרטיס  + [➕ עוד פרטים] [➕ הוסף עוד] [🏠 בית]
```
**למה מסך אחד לתאריך ולא שניים:** בחירת "לועזי/עברי" כמסך נפרד גובה מסך שלם מ‑95% מהמשתמשים כדי לשרת מיעוט. במקום זה — לועזי הוא ברירת המחדל בהקלדה חופשית, והלוח העברי הוא כפתור באותו מסך. מי שצריך עברי מקבל אותו בלחיצה אחת; כל השאר לא משלמים כלום.

"עוד פרטים" (אופציונלי, **אחרי** השמירה) פותח תפריט שדות: קטגוריה, קשר, טלפון, תמונה, הערות, מין, שעת לידה, כינוי, סוג אירוע.

### מפת מסכים
```
                    ┌──────────┐
              ┌────►│ 🏠 בית   │◄────┐
              │     └────┬─────┘     │
   ┌──────────┼──────────┼───────────┼──────────┐
   ▼          ▼          ▼           ▼          ▼
 ➕הוסף   📅רשימה    🔔תזכורות   ⚙️הגדרות   📊סטטיסטיקות
   │          │                     │
   │          ▼                     ├─ שפה
   │      🎴 כרטיס                   ├─ אזור זמן
   │       ├─ ✏️ ערוך                ├─ שעת תזכורת
   │       ├─ 🗑 מחק                 ├─ פורמטים
   │       ├─ 💌 ברכה                ├─ התראות on/off
   │       ├─ 🔔 תזכורות לאירוע      ├─ 💾 גיבוי
   │       └─ 📤 שתף                 └─ 🗑 מחיקת חשבון
   │
   └─ 🔍 חיפוש ─► תוצאות ─► כרטיס
```

---

## 12. Commands

| פקודה | תיאור (BotCommands menu) | הערות |
|-------|--------------------------|-------|
| `/start` | 🏠 התחלה | onboarding או תפריט בית |
| `/add` | ➕ הוספת יום הולדת | קיצור לזרימת הוספה |
| `/list` | 📅 כל התאריכים | |
| `/today` | 🎂 מי חוגג היום | |
| `/week` | 🗓 השבוע הקרוב | |
| `/month` | 📆 החודש | |
| `/search` | 🔍 חיפוש | תומך גם `/search דני` |
| `/reminders` | 🔔 תזכורות | |
| `/settings` | ⚙️ הגדרות | |
| `/stats` | 📊 סטטיסטיקות | |
| `/backup` | 💾 גיבוי וייצוא | |
| `/help` | ❓ עזרה | |
| `/cancel` | ❌ ביטול פעולה | תמיד זמין, מנקה FSM |

**פקודות אדמין (לא ב‑menu):** `/admin`, `/broadcast`, `/userinfo <id>`, `/logs [n]`, `/dbstats`, `/forcebackup`, `/block <id>`, `/unblock <id>`.

**פקודות נסתרות למשתמש:** `/export`, `/import`, `/delete_me`.

> `set_my_commands` נקרא בעלייה, פעם אחת, עם רשימה נפרדת ל‑`he` ול‑`en` (scope: default + language_code).

---

## 13. Callback IDs

### סכימה
`<domain>:<action>[:<arg1>[:<arg2>]]` — עד 64 בייט. **חובה** להשתמש ב‑`CallbackData` factory של aiogram 3, לא במחרוזות ידניות.

מצב תצוגה (מיון/סינון/עמוד אחרון) נשמר ב‑`users.list_sort` / `users.list_filter` ולא ב‑callback — זה שומר על callbacks קצרים ועל המצב אחרי restart.

| Callback | פעולה |
|----------|-------|
| **תפריט** | |
| `mnu:home` | חזרה למסך בית |
| `mnu:add` · `mnu:list` · `mnu:rem` · `mnu:set` · `mnu:srch` · `mnu:stat` · `mnu:help` | ניווט ראשי |
| **הוספה/עריכה** | |
| `ev:type:<type>` | בחירת סוג אירוע |
| `ev:heb` | מעבר למסלול התאריך העברי (כפתור בתוך מסך התאריך, לא מסך בחירה) |
| `ev:hm:<1-13>` | בחירת חודש עברי |
| `ev:hd:<1-30>` | בחירת יום עברי |
| `ev:gm:<1-12>` · `ev:gd:<1-31>` | בחירת חודש/יום לועזי (מסלול כפתורים) |
| `ev:noyear` | "לא יודע את השנה" |
| `ev:cat:<category>` | קטגוריה |
| `ev:gender:<m\|f\|o>` | מין |
| `ev:more` | פתיחת "עוד פרטים" |
| `ev:field:<field>` | עריכת שדה ספציפי |
| `ev:clear:<field>` | ניקוי שדה |
| `ev:skip` · `ev:save` · `ev:cancel` | שליטה בזרימה |
| **כרטיס** | |
| `ev:v:<id>` | הצגת כרטיס |
| `ev:e:<id>` | תפריט עריכה |
| `ev:d:<id>` | בקשת מחיקה |
| `ev:dy:<id>` | אישור מחיקה |
| `ev:undo:<id>` | ביטול מחיקה (soft delete) |
| `ev:gr:<id>` | ברכות לאירוע |
| `ev:sh:<id>` | שיתוף |
| `ev:rem:<id>` | תזכורות לאירוע |
| `ev:mute:<id>` | השתקת אירוע (is_active toggle) |
| **רשימה** | |
| `ls:p:<page>` | דף |
| `ls:sort:<upcoming\|name\|age\|created>` | מיון |
| `ls:filt:<all\|category\|type\|month>` | תפריט סינון |
| `ls:fset:<key>:<val>` | החלת סינון |
| `ls:view:<upcoming\|all\|muted\|trash>` | תצוגה |
| **תזכורות** | |
| `rem:add[:<event_id>]` | הוספת כלל |
| `rem:off:<days>` | בחירת מרווח |
| `rem:time:<HH-MM>` | בחירת שעה (נקודתיים→מקף) |
| `rem:tog:<rule_id>` | הפעלה/כיבוי |
| `rem:del:<rule_id>` | מחיקה |
| **הגדרות** | |
| `set:lang:<he\|en>` · `set:tz:<tz>` · `set:df:<fmt>` · `set:tf:<fmt>` | |
| `set:time:<HH-MM>` · `set:notif:<0\|1>` · `set:silent:<0\|1>` | |
| `set:hebd:<0\|1>` · `set:digest:<0\|1>` | |
| `set:wipe` · `set:wipe_ok` | מחיקת חשבון + אישור |
| **סטטיסטיקות** | `st:home` · `st:months` · `st:cats` · `st:ages` |
| **ברכות** | `tpl:list:<type>` · `tpl:v:<id>` · `tpl:new` · `tpl:del:<id>` · `tpl:use:<tpl>:<ev>` |
| **גיבוי** | `bk:home` · `bk:exp:<json\|csv\|xlsx>` · `bk:imp` · `bk:auto:<0\|1>` |
| **אדמין** | `adm:home` · `adm:stats` · `adm:bc` · `adm:bc_ok` · `adm:logs:<n>` · `adm:u:<id>` |
| **ניווט** | `nav:back` · `nav:home` · `nav:cancel` · `noop` |

**כללי ברזל:**
- כל handler של callback קורא `await callback.answer()` — תמיד, גם בשגיאה.
- כל `<id>` נבדק שייך ל‑`user_id` הנוכחי לפני כל פעולה. אחרת: `answer("האירוע לא נמצא", show_alert=True)`.
- `noop` = כפתור תצוגתי (למשל מספר עמוד) — עונה בלי לעשות כלום.

---

## 14. FSM States

```python
class AddEvent(StatesGroup):
    name = State()
    date = State()           # לועזי בהקלדה חופשית — המסלול הראשי
    heb_month = State()      # מסלול צדדי, רק אחרי [✡️ תאריך עברי]
    heb_day = State()
    heb_year = State()
    # אין state של confirm: שמירה מיידית ברגע שיש שם + תאריך.
    # אין state של calendar: הבחירה היא כפתור בתוך `date`, לא מסך.

class EditEvent(StatesGroup):
    choosing_field = State()
    entering_value = State()
    heb_month = State(); heb_day = State(); heb_year = State()

class Search(StatesGroup):
    query = State()

class SettingsFlow(StatesGroup):
    custom_time = State()
    custom_timezone = State()

class TemplateFlow(StatesGroup):
    body = State()
    tone = State()

class ImportFlow(StatesGroup):
    waiting_file = State()
    confirm = State()

class AdminFlow(StatesGroup):
    broadcast_text = State()
    broadcast_confirm = State()
```

**Storage:** `MemoryStorage` (מספיק — טפסים חיים דקות בודדות; restart מאבד טופס חלקי, וזה מקובל).
**Timeout:** middleware מנקה state שלא נגעו בו מעל 30 דקות ושולח "הפעולה בוטלה בגלל חוסר פעילות 🕐".
**`/cancel` ו‑`nav:cancel`** מנקים state מכל מצב.

---

## 15. Screen Specifications

> פורמט: **מטרה** · **טקסט** · **מקלדת** · **מעברים**. כל הטקסטים ב‑`locales/he.json` — כאן מופיע הערך.

### S1 · מסך בית (`mnu:home`, `/start` למשתמש קיים)

**טקסט:**
```
🏠 <b>בלי פאדיחות</b>

🎂 היום חוגגים: <b>2</b>
📅 השבוע: <b>5</b>
⏭ הקרוב: <b>דנה</b> — עוד 3 ימים

בחר מה לעשות:
```
> אם אין אף אירוע: `עדיין לא הוספת אף אחד. בוא נתחיל 👇` והכפתור הראשון בולט.

**מקלדת (Inline, 2 בשורה):**
```
[ ➕ הוסף ]        [ 📅 הרשימה שלי ]
[ 🔍 חיפוש ]       [ 🔔 תזכורות ]
[ 📊 סטטיסטיקות ]  [ ⚙️ הגדרות ]
[ ❓ עזרה ]
```
**מעברים:** כל כפתור → המסך המתאים, תמיד ב‑`edit_message_text`.

---

### S2 · הוספה — שם (`AddEvent.name`)
```
➕ <b>הוספת תאריך</b>

מה השם?
<i>אפשר גם שם מלא: "דנה כהן"</i>
```
`[❌ ביטול]`
**קלט:** טקסט. מפוצל אוטומטית ל‑first/last לפי רווח ראשון. ולידציה: 1–64 תווים, לא רק אימוג'ים/רווחים.

---

### S3 · הוספה — תאריך (`AddEvent.date`) — **המסך היחיד אחרי השם**
```
📅 מתי נולדה <b>דנה</b>?

כתוב את התאריך, למשל:
<code>15/03/1990</code>
<code>15.3.90</code>
<code>15 במרץ</code>  ← בלי שנה, זה בסדר גמור
```
```
[ 🤷 לא יודע את השנה ]
[ ✡️ תאריך עברי ]
[ ❌ ביטול ]
```
- **הקלדה חופשית** היא המסלול הראשי — לועזי, בלי לבחור כלום.
- `[✡️ תאריך עברי]` → עובר ל‑S4 (בורר עברי). לא מסך חובה, לא שאלה מקדימה.
- `[🤷 לא יודע את השנה]` → הבוט שואל רק יום+חודש (`"15/03"` או בורר), שומר `year=NULL`, ולא מזכיר את זה יותר לעולם.
- ניתן להקליד גם `15/03` בלי שנה ישירות — הפרסר מזהה, בלי צורך בכפתור.

**פרסר (`core/validators.parse_gregorian`) — סדר ניסיונות:**
1. `DD/MM/YYYY`, `DD.MM.YYYY`, `DD-MM-YYYY`
2. `DD/MM/YY` → שנתיים: `00–<current_yy>` ⇒ 20xx, אחרת 19xx
3. `DD/MM` או `DD.MM` → בלי שנה
4. `<day> ב<חודש בעברית>` / `<day> <month name en>`
5. `YYYY-MM-DD` (ISO)

שגיאה → `❌ לא הצלחתי לקרוא את התאריך. נסה בפורמט 15/03/1990` (בלי לצאת מה‑state).

---

### S4 · הוספה — תאריך עברי (מסלול צדדי, נכנסים אליו רק בלחיצה על `[✡️ תאריך עברי]`)
**חודש (`AddEvent.heb_month`):**
```
✡️ באיזה חודש עברי?
```
```
[ניסן] [אייר] [סיוון]
[תמוז] [אב]   [אלול]
[תשרי] [חשוון][כסלו]
[טבת]  [שבט]  [אדר]
[← חזרה]
```
> "אדר" מציג תת־בחירה `[אדר א׳] [אדר ב׳] [סתם אדר]` רק אם המשתמש לוחץ עליו; "סתם אדר" = `month=12` עם `adar_policy` בברירת מחדל.

**יום (`AddEvent.heb_day`):** גריד 5 בשורה, 1..`month_length` (29 או 30), עם גימטריה: `[א׳][ב׳][ג׳]...`
**שנה (`AddEvent.heb_year`):** `[🤷 לא יודע את השנה]` **כפתור ראשון, רחב, בשורה נפרדת** + הקלדה. מקבל `5750` או `1990`.

> גם במסלול העברי — השנה אופציונלית, ודילוג עליה מסיים את ההוספה מיד.

---

### S5 · הוספה — נשמר (מסך תוצאה, לא מסך אישור)
> **אין שלב "אשר שמירה".** ברגע שיש שם + תאריך, האירוע נשמר ל‑DB והמסך הזה מוצג כעובדה מוגמרת.
```
✅ <b>נוסף בהצלחה!</b>

🎂 <b>דנה כהן</b>
📅 15/03/1990  (י״ט באדר תש״ן)
⏳ עוד <b>34 ימים</b>
🎈 תחגוג <b>36</b>

🔔 תזכורת: יום לפני, ב‑09:00
```
```
[ ➕ עוד פרטים ]  [ 🔔 שנה תזכורת ]
[ ➕ הוסף עוד ]   [ 🏠 בית ]
```

---

### S6 · "עוד פרטים" (`ev:more`)
```
✏️ <b>דנה כהן</b> — פרטים נוספים
מה להוסיף?
```
```
[🏷 קטגוריה: משפחה]   [👤 קשר: —]
[📞 טלפון: —]         [💬 כינוי: —]
[🖼 תמונה: —]         [📝 הערות: —]
[⚧ מין: —]            [🕐 שעת לידה: —]
[🎯 סוג: יום הולדת]
[✅ סיימתי]
```
כל כפתור מציג את הערך הנוכחי. לחיצה → `EditEvent.entering_value` עם prompt מותאם + `[דלג ←]` `[🗑 נקה]` `[← חזרה]`.

**המסך הזה אינו חלק מזרימת ההוספה** — הוא מוצע אחרי שהאירוע כבר נשמר, ואפשר לצאת ממנו בכל רגע בלי למלא כלום. אין ספירת "השלמת 3 מתוך 9", אין progress bar, אין נודניק.

---

### S7 · רשימה (`mnu:list`, `ls:p:<n>`)
```
📅 <b>הרשימה שלי</b>  ·  47 אנשים
מיון: הקרובים ביותר  ·  סינון: הכל

🎂 <b>דנה כהן</b> — היום! (36)
1️⃣ <b>יוסי לוי</b> — מחר (41)
3️⃣ <b>מיכל</b> — עוד 3 ימים (29)
7️⃣ <b>אבא</b> — עוד 7 ימים (68)
...
```
כל שורה גם ככפתור בפני עצמו (`ev:v:<id>`), 8 בעמוד.
```
[🎂 דנה כהן — היום (36)]
[1️⃣ יוסי לוי — מחר (41)]
... ×8
[◀️] [ 2/6 ] [▶️]
[⇅ מיון] [🔽 סינון] [🔍 חיפוש]
[🏠 בית]
```
**סינון (`ls:filt`):** קטגוריה · סוג אירוע · חודש · "רק החודש" · "בלי שנה" · "מושתקים" · "🗑 סל מחזור".
**מיון:** הקרובים · א‑ב · גיל · תאריך הוספה.

---

### S8 · כרטיס אירוע (`ev:v:<id>`)
אם יש `photo_file_id` → `send_photo` עם caption; אחרת הודעת טקסט.
```
🎂 <b>דנה כהן</b>  <i>(דנוש)</i>

📅 15/03/1990  ·  י״ט באדר תש״ן
⏳ עוד <b>34 ימים</b>  (יום ראשון)
🎈 תחגוג <b>36</b>
🏷 משפחה · אחות
📞 050-1234567
💬 @dana
📝 אוהבת שוקולד מריר

🔔 תזכורות: יום לפני · ביום עצמו
```
```
[ ✏️ ערוך ]      [ 💌 ברכה ]
[ 🔔 תזכורות ]   [ 🔕 השתק ]
[ 📤 שתף ]       [ 🗑 מחק ]
[ ← לרשימה ]     [ 🏠 בית ]
```
שדות ריקים **לא מוצגים בכלל** (בלי "—" בכרטיס התצוגה).

---

### S9 · מחיקה (`ev:d:<id>`)
```
🗑 למחוק את <b>דנה כהן</b>?

הפריט יעבור לסל המחזור ל‑30 יום,
ואפשר לשחזר בכל רגע.
```
`[✅ כן, מחק] [❌ ביטול]`
אחרי מחיקה: `🗑 דנה כהן נמחקה.` + `[↩️ בטל מחיקה]` `[← לרשימה]`

---

### S10 · חיפוש (`mnu:srch`, `Search.query`)
```
🔍 <b>חיפוש</b>

כתוב שם, כינוי, טלפון, קטגוריה או חודש.
<i>לדוגמה: "דנה", "משפחה", "מרץ", "050"</i>
```
**לוגיקה:** חיפוש `LIKE %q%` case-insensitive על first/last/nickname/phone/notes/relation; אם ה‑query תואם שם קטגוריה או שם חודש (עברי או לועזי) — מסנן לפיהם. תוצאות: אותו רינדור כמו S7.
אין תוצאות → `😕 לא נמצא כלום עבור "<b>xyz</b>"` + `[🔍 חיפוש חדש] [🏠 בית]`

---

### S11 · תזכורות (`mnu:rem`)
```
🔔 <b>תזכורות</b>

התזכורות שיישלחו על כל אירוע:

✅ יום לפני   · 09:00
✅ ביום עצמו · 09:00
⬜ שבוע לפני · 09:00

<i>אפשר גם תזכורות מיוחדות לאירוע ספציפי,
מתוך הכרטיס שלו.</i>
```
```
[✅ יום לפני · 09:00]     ← toggle
[✅ ביום עצמו · 09:00]
[⬜ שבוע לפני · 09:00]
[➕ הוסף תזכורת]
[🔕 כבה הכל]  [🏠 בית]
```
**הוספה (`rem:add`) — לחיצה אחת, לא אשף:**
```
➕ מתי להזכיר?

[ביום עצמו] [יום לפני]
[יומיים]    [3 ימים]
[שבוע]      [שבועיים]
[חודש]
[← חזרה]
```
בחירת מרווח = **סיום**. הכלל נשמר מיד ב‑`send_time=NULL` (כלומר שעת ברירת המחדל של המשתמש), והמסך חוזר לרשימת התזכורות עם הודעה `✅ נוסף: שבוע לפני · 09:00`.

**בחירת שעה היא לא שלב בזרימה.** מי שרוצה שעה אחרת לוחץ על הכלל שנוצר ומשנה — `[🕐 שנה שעה]` → `[08:00][09:00][10:00][12:00][18:00][20:00][🕐 אחרת]`.

> **אסור** להפוך את בחירת השעה לשלב חובה אחרי בחירת המרווח. 90% מהמשתמשים רוצים את שעת ברירת המחדל שכבר בחרו באונבורדינג, ואין שום סיבה לשאול אותם פעמיים.

מקסימום 5 כללים גלובליים → מעבר לזה: `הגעת למקסימום של 5 תזכורות. מחק אחת כדי להוסיף חדשה.`

---

### S12 · הגדרות (`mnu:set`)
```
⚙️ <b>הגדרות</b>
```
```
[🌐 שפה: עברית]
[🕐 אזור זמן: ישראל]
[⏰ שעת תזכורת: 09:00]
[📅 פורמט תאריך: 15/03/1990]
[🕑 פורמט שעה: 24 שעות]
[✡️ תאריך עברי בכרטיס: ✅]
[🔔 התראות: ✅]
[🔕 התראות שקטות: ⬜]
[📰 סיכום יומי: ⬜]
[💾 גיבוי וייצוא]
[🗑 מחיקת החשבון]
[🏠 בית]
```
כל כפתור מציג את הערך הנוכחי ומחליף/פותח בורר. **שינוי נשמר מיד** — אין "שמור".

---

### S13 · סטטיסטיקות (`mnu:stat`)
```
📊 <b>סטטיסטיקות</b>

👥 סה"כ: <b>47</b>
🎂 היום: <b>2</b>
📅 השבוע: <b>5</b>
📆 החודש: <b>9</b>

⏭ הקרוב: <b>דנה כהן</b> — עוד 3 ימים
🎈 הצעיר ביותר: <b>נועם</b> (4)
👴 המבוגר ביותר: <b>סבתא</b> (89)
📈 גיל ממוצע: <b>34</b>

🏷 לפי קטגוריה:
משפחה 18 · חברים 15 · עבודה 9 · לקוחות 5

📅 לפי חודש:
ינו ▓▓▓ 3   פבר ▓▓ 2   מרץ ▓▓▓▓▓ 5
...
```
`[📆 לפי חודשים] [🏷 לפי קטגוריות] [🎈 גילאים] [🏠 בית]`

---

### S14 · ברכות (`ev:gr:<id>`)
```
💌 <b>ברכה לדנה</b>

בחר סגנון, ואני אכין לך טקסט מוכן להעתקה:
```
`[💖 חם] [😄 מצחיק] [👔 רשמי] [⚡ קצר] [✏️ שלי] [← חזרה]`
בחירה →
```
💌 מוכן להעתקה:

<code>דנה יקרה, יום הולדת שמח! 🎉
שתהיה לך שנה מלאה בבריאות,
אושר והצלחה. אוהבים אותך ❤️</code>

<i>לחיצה ארוכה על הטקסט → העתק</i>
```
`[🔄 עוד אחת] [📤 שלח לצ׳אט אחר] [← חזרה]`
> "שלח לצ׳אט אחר" = כפתור `switch_inline_query` שפותח את בורר הצ׳אטים של טלגרם עם הטקסט מוכן. **הבוט לא שולח לאף אחד בעצמו.**

---

### S15 · גיבוי (`bk:home`)
```
💾 <b>גיבוי וייצוא</b>

📦 47 רשומות
🕐 גיבוי אוטומטי אחרון: היום 03:30
```
`[📄 JSON] [📊 CSV] [📗 Excel]` · `[📥 ייבוא מקובץ]` · `[🔄 גיבוי אוטומטי: ✅]` · `[← הגדרות]`

---

### S16 · הודעת תזכורת (הפוש עצמו)
```
🎂 <b>היום יום ההולדת של דנה כהן!</b>

🎈 היא חוגגת <b>36</b>
🏷 משפחה · אחות
📞 050-1234567
```
`[💌 ברכה] [👤 הכרטיס] [🔕 השתק]`

**וריאנטים לפי `offset_days`:**
| מרווח | כותרת |
|-------|-------|
| 0 | `🎂 היום יום ההולדת של <b>{name}</b>!` |
| 1 | `🎁 מחר יום ההולדת של <b>{name}</b>` |
| 2 | `🎁 בעוד יומיים — יום ההולדת של <b>{name}</b>` |
| 3–6 | `📅 בעוד {n} ימים — יום ההולדת של <b>{name}</b>` |
| 7 | `🥳 בעוד שבוע — יום ההולדת של <b>{name}</b>` |
| 14 | `🗓 בעוד שבועיים — יום ההולדת של <b>{name}</b>` |
| 30 | `🗓 בעוד חודש — יום ההולדת של <b>{name}</b>` |

**לפי סוג אירוע:** `anniversary` → `💍 יום נישואין`, `wedding` → `💒 יום החתונה`, `memorial` → `🕯 אזכרה` (בלי אימוג'י חגיגי, בלי "מזל טוב", ניסוח מכבד), `custom` → `📌 {custom_type_label}`.

**התאמת מין:** `gender=f` → "היא חוגגת", `m` → "הוא חוגג", NULL → "חוגג/ת".

---

### S17 · סיכום יומי (אופציונלי)
```
☀️ <b>בוקר טוב!</b>

היום:
🎂 דנה כהן (36)
🎂 יוסי לוי (41)

השבוע:
📅 מיכל — עוד 3 ימים
📅 אבא — עוד 5 ימים
```
נשלח רק אם יש תוכן. אין אירועים → לא נשלח כלום.

---

### S18 · עזרה (`mnu:help`)
טקסט קצר (עד 15 שורות): מה הבוט עושה, איך מוסיפים, איך משנים תזכורת, איך מגבים, איך פונים לתמיכה. `[➕ הוסף ראשון] [🏠 בית]`

---

### S19 · אדמין (`/admin`)
```
🛠 <b>ניהול</b>

👥 משתמשים: 312  (פעילים 30 יום: 187)
🎂 אירועים: 4,208
🔔 תזכורות נשלחו היום: 156  (נכשלו: 2)
💾 DB: 4.2 MB  ·  גיבוי אחרון: היום 03:30
⏱ Uptime: 6d 4h
```
`[📊 סטטיסטיקות] [📢 הודעה לכולם] [📜 לוגים] [👤 חיפוש משתמש] [💾 גיבוי עכשיו]`

---

## 16. Messages & Copy

### עקרונות ניסוח
- **גוף שני, ידידותי, קצר.** "בוא נוסיף" ולא "אנא הזן".
- **מקסימום 5–7 שורות בהודעה.** יותר מזה = פצל למסכים.
- **אימוג'י אחד בתחילת שורה, לא באמצע משפט.** לא יותר מ‑4 בהודעה.
- **בלי "מערכת", "שגיאה מספר 500", "פעולה בוצעה בהצלחה".** הודעה אנושית.
- **שגיאה תמיד מציעה מה לעשות:** `❌ לא הצלחתי לקרוא את התאריך. נסה 15/03/1990`

### מחרוזות שחייבות להיות מדויקות
| מפתח | עברית |
|------|-------|
| `common.back` | `← חזרה` |
| `common.home` | `🏠 בית` |
| `common.cancel` | `❌ ביטול` |
| `common.saved` | `✅ נשמר` |
| `common.deleted` | `🗑 נמחק` |
| `common.yes` / `common.no` | `✅ כן` / `❌ לא` |
| `common.skip` | `דלג ←` |
| `common.unknown` | `לא ידוע` |
| `error.generic` | `😕 משהו השתבש. נסה שוב בעוד רגע.` |
| `error.not_found` | `הפריט הזה כבר לא קיים.` |
| `error.rate_limit` | `רגע, נשמה 😅 קצת לאט יותר.` |
| `error.too_long` | `זה ארוך מדי — עד {max} תווים.` |
| `error.limit_reached` | `הגעת למקסימום {max}.` |
| `fsm.timeout` | `🕐 הפעולה בוטלה בגלל חוסר פעילות.` |

### ריבוי (pluralization) בעברית
`core/text.py` מטפל: `1 יום` / `2 ימים` / `יומיים` (מקרה מיוחד!) / `5 ימים`. אותו דבר ל"שנה/שנתיים/שנים", "שבוע/שבועיים/שבועות", "אדם/אנשים".

---

## 17. Scheduler

`AsyncIOScheduler` שעולה ב‑`main.py` אחרי אתחול ה‑bot ולפני ה‑polling.

| Job | תדירות | תיאור |
|-----|--------|-------|
| `tick_reminders` | כל 60 שניות | מנוע התזכורות (פרק 18) |
| `recompute_occurrences` | יומי 02:00 UTC | מחשב מחדש `events.next_occurrence` לכל האירועים הפעילים |
| `daily_digest` | כל 15 דקות | שולח סיכום למשתמשים שה‑`digest_time` המקומי שלהם חל בחלון |
| `auto_backup` | יומי לפי `AUTO_BACKUP_TIME` | `VACUUM INTO` + ניקוי ישנים |
| `purge_soft_deleted` | יומי 04:00 UTC | מוחק סופית אירועים עם `deleted_at < now-30d` |
| `cleanup_logs` | שבועי | מוחק `audit_logs` מעל 90 יום, `notifications_log` מעל 180 יום |
| `sync_admins` | בעלייה בלבד | מסנכרן `is_admin` מ‑`ADMIN_IDS` |

**כללים:**
- `max_instances=1` + `coalesce=True` לכל job (מונע חפיפה).
- `misfire_grace_time=300`.
- כל job עטוף ב‑try/except שמדווח לאדמין ולא מפיל את ה‑scheduler.
- `recompute_occurrences` גם נקרא ידנית אחרי כל create/update של אירוע.
- ה‑scheduler נסגר נקי ב‑`shutdown(wait=True)` על SIGTERM.

---

## 18. Reminder Engine

זה הרכיב הכי קריטי. אלגוריתם ה‑tick:

```
tick_reminders(now_utc):
  1. שלוף משתמשים פעילים: notifications_enabled=1 AND is_blocked=0
                            AND bot_blocked_by_user=0
  2. לכל משתמש:
     tz        = ZoneInfo(user.timezone)
     now_local = now_utc.astimezone(tz)
     today     = now_local.date()

     events = repo.active_events(user_id,
                 next_occurrence BETWEEN today AND today + MAX_UPCOMING_DAYS)

     rules  = global_rules(user) + per_event_rules(user)
              # כלל ספציפי לאירוע גובר על גלובלי עם אותו offset_days

     for event in events:
       occ = event.next_occurrence
       for rule in rules_for(event):
         if rule.offset_days is not None:
             fire_local = datetime.combine(
                 occ - timedelta(days=rule.offset_days),
                 parse_time(rule.send_time or user.default_notify_time))
         else:                                   # offset_minutes
             if not event.event_time: continue
             fire_local = (datetime.combine(occ, parse_time(event.event_time))
                           - timedelta(minutes=rule.offset_minutes))

         fire_utc = fire_local.replace(tzinfo=tz).astimezone(UTC)

         if fire_utc > now_utc:               continue   # עוד לא הגיע
         if now_utc - fire_utc > GRACE:       mark_skipped(); continue
         if already_logged(event, rule, occ): continue   # UNIQUE index

         INSERT notifications_log(status='pending', ...)   ← קודם רשומה, אז שליחה
         enqueue_send(user, event, rule, occ)

  3. שלח את התור דרך notify_service (rate limit גלובלי, ראה למטה)
  4. עדכן status='sent' + sent_at, או 'failed' + error
  5. אם occ == today ו‑offset_days == 0 → recompute next_occurrence לשנה הבאה
```

### עקרונות ברזל
| עיקרון | מימוש |
|--------|-------|
| **בדיוק פעם אחת** | `UNIQUE(event_id, rule_id, occurrence_date)` — הרשומה נכתבת **לפני** השליחה |
| **התאוששות מ‑downtime** | תזכורת שפוספסה נשלחת אם עברו ≤ `REMINDER_GRACE_HOURS` (6 שעות). מעבר לזה → `skipped` (עדיף לא לשלוח "מחר יום הולדת" יומיים אחרי) |
| **אין ספאם** | אותו אירוע לא ייצור שתי הודעות באותה דקה — אם שני כללים נופלים באותה דקה, מאחדים להודעה אחת |
| **שעון קיץ** | ההמרה ל‑UTC מחושבת בכל tick מחדש, אף פעם לא נשמרת |
| **קצב** | `AsyncRateLimiter` גלובלי: 20 הודעות/שנייה. תור אחד לכל השליחות |
| **retry** | `TelegramRetryAfter` → sleep + retry (עד 3). `TelegramForbiddenError` → `bot_blocked_by_user=1`, `notifications_enabled=0`, status=`failed` |
| **תדירות** | ה‑tick חייב לרוץ בפחות מ‑10 שניות ב‑1000 משתמשים. אם לא — פיצול לבאצ'ים |

### `notify_service.send()`
```python
async def send(user, event, rule, occurrence) -> bool:
    text = render_reminder(user, event, rule, occurrence)
    kb   = reminder_keyboard(event.id)
    await limiter.acquire()
    await bot.send_message(user.id, text, reply_markup=kb,
                           parse_mode="HTML",
                           disable_notification=user.silent_notifications)
```

---

## 19. Localization (i18n)

- קבצי `locales/he.json` ו‑`locales/en.json` — מבנה שטוח עם מפתחות מנוקדים: `"screen.home.title"`.
- `he.json` הוא **מקור האמת**. טסט נכשל אם קיים מפתח ב‑`he` שאין ב‑`en` או להפך.
- `translator.t(key, lang, **kwargs)` — `str.format`. מפתח חסר → מחזיר את המפתח עצמו ורושם `WARNING` (לא קורס).
- `I18nMiddleware` מזריק `_` לכל handler:
  ```python
  await message.answer(_("screen.home.title"))
  ```
- **הכל בקבצי locale** — אפס מחרוזת עברית hardcoded בקוד, כולל טקסטים של כפתורים ושגיאות.
- שמות חודשים עבריים ולועזיים, שמות ימי שבוע, שמות קטגוריות — הכל בקובץ locale.
- ה‑fallback הוא `he`.

### RTL
- כל הודעה שמערבת עברית ומספרים/תאריכים תתחיל ב‑RLM (`‏`) כדי למנוע היפוך.
- טלפונים, `@username` ותאריכים לועזיים עטופים ב‑LRM (`‎`) משני הצדדים.
- `core/formatting.rtl(text)` ו‑`ltr(text)` מטפלים בזה — **אסור** לשרשר ידנית.

---

## 20. Settings

| הגדרה | ערכים | ברירת מחדל | השפעה |
|-------|-------|------------|-------|
| שפה | he / en | he | כל הטקסטים, שמות חודשים |
| אזור זמן | IANA | Asia/Jerusalem | חישוב "היום" ושעת שליחה |
| שעת תזכורת ברירת מחדל | HH:MM | 09:00 | כללים עם `send_time=NULL` |
| פורמט תאריך | DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD | DD/MM/YYYY | תצוגה בלבד |
| פורמט שעה | 24h / 12h | 24h | תצוגה בלבד |
| תאריך עברי בכרטיס | on/off | on | הצגת התאריך המקביל |
| התראות | on/off | on | כיבוי גורף (המידע נשמר) |
| התראות שקטות | on/off | off | `disable_notification` |
| סיכום יומי | on/off + שעה | off / 08:00 | job נפרד |
| מדיניות אדר | adar_i / adar_ii | adar_ii | חישוב מופע בשנה מעוברת |
| מדיניות 29/2 | feb28 / mar01 | feb28 | חישוב מופע בשנה לא מעוברת |

**בורר אזור זמן:** כפתורים מהירים `[🇮🇱 ישראל] [🇺🇸 ניו יורק] [🇬🇧 לונדון] [🌍 אחר]`. "אחר" → הקלדה עם השלמה לפי `zoneinfo.available_timezones()`.

**מחיקת חשבון (`set:wipe`):** אזהרה מפורשת → הקלדת המילה `מחק` → מחיקה מלאה (CASCADE) + הצעת ייצוא JSON לפני כן.

---

## 21. Statistics

`stats_service.get_user_stats(user_id) -> UserStats`:

| שדה | חישוב |
|-----|-------|
| `total` | `COUNT(*) WHERE deleted_at IS NULL` |
| `today` / `this_week` / `this_month` | לפי `next_occurrence` ב‑tz של המשתמש |
| `next_30_days` | |
| `nearest` | `ORDER BY next_occurrence LIMIT 1` |
| `by_category` | `GROUP BY category` |
| `by_type` | `GROUP BY event_type` |
| `by_month` | `GROUP BY month` (של המופע, לא של הלידה) |
| `youngest` / `oldest` / `avg_age` | רק על אירועים עם `year IS NOT NULL` |
| `without_year` | כמה חסרי שנה (עם CTA "השלם פרטים") |
| `muted` | כמה מושתקים |

**גרף חודשים:** בר‑צ'ארט ASCII עם `▓` (מקסימום 10 תווים, מנורמל למקסימום). בלי ספריות גרפים.

---

## 22. Templates (ברכות)

- **תבניות מערכת (seed)** — נטענות במיגרציה הראשונה. מינימום: 6 לכל שילוב של `event_type × tone` בעברית, 3 באנגלית.
- **placeholders:** `{name}`, `{nickname}`, `{age}`, `{relation}`. חסר ערך → הביטוי מושמט בעדינות (`{age}` חסר → מוחקים את המשפט שמכיל אותו).
- **תבניות אישיות:** המשתמש יכול ליצור/למחוק (`tpl:new`) — עד 20.
- **בחירה:** רנדומלית מתוך התבניות התואמות `event_type + tone + gender + language`, בלי לחזור על אותה תבנית פעמיים ברצף לאותו אירוע.
- **הבוט לא שולח ברכה בשם המשתמש.** רק מציג טקסט להעתקה + כפתור `switch_inline_query` לשיתוף.
- `memorial` → אין ברכות. הכפתור לא מוצג.

---

## 23. Backup System

### ייצוא
| פורמט | תוכן |
|-------|------|
| **JSON** | מלא: user settings + events + rules + templates. `schema_version` בראש. זה הפורמט לייבוא. |
| **CSV** | events בלבד, UTF‑8 **עם BOM** (שאקסל בעברית לא ישבור), כותרות בעברית |
| **XLSX** | גיליון `אירועים` + גיליון `סיכום`, עמודות ברוחב מותאם, RTL sheet |

שם קובץ: `birthly_{user_id}_{YYYYMMDD_HHMM}.{ext}`. נשלח כ‑document, נמחק מהדיסק אחרי השליחה.

### תמונות — לא מיוצאות (החלטה סופית)
הבוט שומר `photo_file_id` בלבד ולא מוריד קבצי מדיה. לכן **תמונות אינן נכללות בשום ייצוא** — לא ב‑JSON, לא ב‑CSV, לא ב‑XLSX.

| היבט | התנהגות |
|------|---------|
| ייצוא | שדה `photo_file_id` **מושמט לגמרי** מקובץ הייצוא. לא מייצאים מזהה שחסר לו הקשר. |
| ייבוא | אם קובץ ייבוא מכיל `photo_file_id` (למשל מגרסה עתידית) — הוא מתעלם ממנו בשקט. |
| הודעה למשתמש בייצוא | שורה אחת בסוף הודעת הייצוא: `<i>שים לב: תמונות לא נכללות בקובץ.</i>` — פעם אחת, בלי דיאלוג אישור ובלי אזהרה מודגשת. |
| מחיקת חשבון | ה‑`file_id` נמחק עם הרשומה. התמונה עצמה נשארת בשרתי טלגרם ואינה בשליטת הבוט — זה מתועד ב‑`/help`. |

### ייבוא (`bk:imp`)
1. המשתמש שולח קובץ JSON/CSV (עד 5MB).
2. הבוט מנתח ומציג תצוגה מקדימה: `נמצאו 47 רשומות · 3 כפילויות · 1 שגויה`.
3. בחירת מצב: `[➕ הוסף לקיים] [🔄 החלף הכל] [❌ ביטול]`.
4. "החלף הכל" דורש אישור נוסף + מבצע גיבוי אוטומטי לפני.
5. זיהוי כפילות: `(first_name, last_name, month, day, calendar_type)`.
6. שורה שגויה לא מפילה את הייבוא — נאספת לדוח: `יובאו 44, דולגו 3 (שגיאות בשורות 12, 19, 31)`.

### גיבוי מערכת אוטומטי
`VACUUM INTO 'data/backups/birthly_YYYYMMDD.db'` יומי, שמירת `BACKUP_RETENTION_DAYS`. `VACUUM INTO` בטוח תוך כדי ריצה (בניגוד להעתקת קובץ).

---

## 24. Admin

- הרשאה מ‑`ADMIN_IDS` ב‑`.env`, מסונכרן ל‑`users.is_admin` בעלייה. **פילטר `IsAdmin` על ה‑Router כולו**, לא בדיקה בכל handler.
- **Broadcast:** הקלדת טקסט → תצוגה מקדימה מרונדרת → `[✅ שלח ל‑312 משתמשים] [❌ ביטול]` → שליחה ב‑20/שנייה עם דיווח התקדמות כל 50 → סיכום `נשלח: 305 · חסמו: 7`.
- **חיפוש משתמש:** `/userinfo <id|@username>` → פרטים, מספר אירועים, פעילות אחרונה, כפתורי חסימה/שחרור.
- **לוגים:** `/logs 50` → 50 השורות האחרונות כקובץ (לא כהודעה).
- **התראות אוטומטיות לאדמין:** exception לא מטופל, כישלון של job, DB מעל 500MB, שיעור כישלון תזכורות מעל 5%.
- **אין מחיקת נתוני משתמש מהאדמין** — רק חסימה. מחיקה היא זכות המשתמש בלבד.

---

## 25. Logging

### שני יעדים
1. **קובץ** `data/logs/bot.log` — JSON, `RotatingFileHandler(10MB × 5)`.
2. **stdout** — טקסט קריא, נאסף ע"י journald.

### שדות בכל רשומה
`timestamp`, `level`, `logger`, `event`, `user_id`, `update_id` (correlation), `handler`, `duration_ms`, `extra`.

### מה נרשם
| רמה | מתי |
|-----|-----|
| DEBUG | תוכן update מלא (רק ב‑`ENV=development`) |
| INFO | כל handler שנכנס, כל תזכורת שנשלחה, כל job שהסתיים, start/stop |
| WARNING | ולידציה נכשלה, rate limit, מפתח i18n חסר, תזכורת שדולגה |
| ERROR | חריגה מטופלת, כישלון שליחה, כישלון job |
| CRITICAL | קריסת bootstrap, DB לא נגיש |

### `audit_logs` (בנפרד מהקובץ)
פעולות עסקיות בלבד — יצירה/עדכון/מחיקה/ייצוא/ייבוא/שינוי הגדרות/תזכורת שנשלחה. משמש ל"היסטוריה" ולדיבוג תלונות. **אסור לרשום PII מיותר** — לא טלפונים, לא הערות; רק `entity_id` ושדות שהשתנו.

### מה אסור לרשום לעולם
`BOT_TOKEN`, תוכן הערות, מספרי טלפון, תוכן הודעות פרטיות של המשתמש.

---

## 26. Error Handling

### שכבות
1. **ולידציה** (`core/validators`) — זורק `ValidationError` עם הודעה ידידותית בעברית. ה‑handler תופס ומציג בלי לצאת מה‑state.
2. **Handler** — `try/except` סביב קריאות לשירותים. `NotFoundError` → "הפריט כבר לא קיים". `LimitError` → "הגעת למקסימום".
3. **Global** — `@dp.errors()` תופס הכל: לוג ERROR + מזהה שגיאה קצר + הודעה למשתמש `😕 משהו השתבש. נסה שוב בעוד רגע. (קוד: A7F2)` + דיווח לאדמין.

### חריגות טלגרם
| חריגה | טיפול |
|-------|-------|
| `TelegramRetryAfter` | sleep(retry_after + 1), retry ×3 |
| `TelegramForbiddenError` | `bot_blocked_by_user=1`, כיבוי התראות, בלי retry |
| `TelegramBadRequest: message is not modified` | **מתעלמים בשקט** (מצב נפוץ ולגיטימי בעריכת מסך) |
| `TelegramBadRequest: message to edit not found` | שולחים הודעה חדשה במקום |
| `TelegramNetworkError` | retry עם exponential backoff |

### DB
`IntegrityError` על ה‑UNIQUE של תזכורות = מצב תקין (מישהו כבר שלח) → DEBUG, לא ERROR. שאר `SQLAlchemyError` → rollback + ERROR + הודעה גנרית.

### עקרונות
- **הבוט לא קורס לעולם בגלל update בודד.**
- **אין stack trace למשתמש.**
- **כל שגיאה מציעה צעד הבא.**

---

## 27. Security

| נושא | מימוש |
|------|-------|
| **בידוד נתונים** | `BaseRepository` מקבל `user_id` בבנאי; כל method מוסיף `WHERE user_id = :uid` אוטומטית. אין דרך לשלוף לפי `id` בלבד. |
| **IDOR** | כל `<id>` מ‑callback עובר `get_owned(id, user_id)` → `NotFoundError` אם לא שייך. **חובה, גם אם ה‑ID "לא ניתן לניחוש".** |
| **Injection** | SQLAlchemy עם פרמטרים בלבד. אפס string formatting של SQL. |
| **XSS / HTML injection** | `parse_mode=HTML` + `html.escape()` על **כל** קלט משתמש לפני שילוב בהודעה. `core/text.esc()` — חובה. |
| **Rate limiting** | `ThrottlingMiddleware`: 20 הודעות/דקה, 40 callbacks/דקה, לכל user_id. חריגה → הודעה אחת ואז השתקה ל‑30 שניות (בלי להציף). |
| **ולידציית קלט** | אורכים: name 64, nickname 32, notes 500, phone 20, relation 32. תווי בקרה מסוננים. אימוג'י מותרים. שנה 1900–2100. |
| **קבצים** | ייבוא: עד 5MB, סיומת מותרת בלבד, JSON parsing עם `json.loads` בלבד (אין `eval`/`pickle`). תמונות: שומרים `file_id` בלבד — הבוט לא מוריד ולא כותב קבצי מדיה לדיסק. |
| **סודות** | `.env` ב‑`.gitignore`, הרשאות `600`, בעלות `birthly:birthly`. הטוקן לא נכנס ללוג לעולם. |
| **DB** | `data/` בהרשאות `700`, קובץ DB `600`. |
| **אדמין** | allowlist מפורש. פילטר ברמת Router. |
| **חסימה** | `is_blocked=1` → כל update נענה בהודעה קצרה ומסתיים ב‑middleware. |
| **פרטיות** | `/delete_me` מוחק הכל CASCADE, בלי שאריות. הבוט לא אוסף שום דבר מעבר למה שהמשתמש הזין. |
| **תלויות** | `pip-audit` לפני deploy. |

---

## 28. Coding Standards

- **Python 3.12**, type hints מלאים. `mypy --strict` על `core/` ו‑`services/`.
- **ruff** לפורמט ולינט, שורה עד 100 תווים.
- **שמות:** `snake_case` לפונקציות/משתנים, `PascalCase` למחלקות, `UPPER_SNAKE` לקבועים.
- **async לכל האורך.** אפס I/O חוסם ב‑event loop. פעולה כבדה (Excel, ייבוא גדול) → `asyncio.to_thread`.
- **פונקציה = עד 40 שורות.** ארוך יותר = לפצל.
- **אין לוגיקה ב‑handlers.** handler = פרסור קלט → קריאה ל‑service → רינדור. אם handler עולה על 30 שורות, משהו לא במקום.
- **`core/` טהור:** בלי DB, בלי I/O, בלי aiogram. זה מה שמאפשר טסטים אמיתיים.
- **Docstrings** על כל פונקציה ציבורית ב‑`core/` ו‑`services/` — מה נכנס, מה יוצא, מה זורק.
- **Enums ב‑`constants.py`** לכל ערך סגור (`EventType`, `Category`, `CalendarType`, `Tone`, `NotificationStatus`).
- **בלי מספרי קסם.** בלי מחרוזות עברית בקוד.
- **Imports:** stdlib → third‑party → local, מופרדים בשורה ריקה.
- **קומיטים:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).

---

## 29. UX Rules

0. **חוזה הפשטות (פרק 11.1) גובר על כל כלל אחר.** רק שם ותאריך הם חובה. לכל שאלה אחרת יש `דלג ←`, והדילוג לא עולה למשתמש בכלום.
1. **אף מסך בלי דרך חזרה.** `← חזרה` או `🏠 בית` בכל מסך, בשורה האחרונה.
2. **עורכים את ההודעה הקיימת** (`edit_message_text`) במקום לשלוח חדשה. הצ'אט לא מתמלא.
3. **מקסימום 2 כפתורים בשורה**, 8 כפתורים במסך. יותר → דפדוף.
4. **כל פעולה הרסנית דורשת אישור**, וכל מחיקה ניתנת לביטול (soft delete + `↩️ בטל`).
5. **הוספת אירוע = 2 מסכים. הוספת תזכורת = לחיצה אחת.** אם זרימה גדלה — משהו הפך לחובה שלא היה צריך.
6. **הכפתור מציג את הערך הנוכחי**: `[🌐 שפה: עברית]` ולא `[🌐 שפה]`.
7. **תמיד `callback.answer()`** — אחרת המשתמש רואה "טוען" תקוע.
8. **פעולה שלוקחת יותר משנייה** → `callback.answer("רגע...")` או `send_chat_action`.
9. **אמוג'י כמשמעות, לא כקישוט.** אותו אימוג'י תמיד לאותו מושג (טבלה בפרק 30).
10. **מצב ריק תמיד עם CTA**, לעולם לא "אין נתונים" יבש.
11. **הקלדה חופשית תמיד עם דוגמה** בהודעה עצמה.
12. **הבוט לא שואל שאלה בלי כפתור בריחה** (`דלג ←` / `❌ ביטול`), וכפתור הדילוג רחב ובשורה נפרדת — לא מוסתר בפינה.
13. **מספרים בעברית מנוסחים נכון**: "עוד יומיים", לא "עוד 2 ימים".
14. **המסך הראשון מציג ערך מיידי** — מי חוגג היום, לפני כל כפתור.
15. **אין הצקה על שדות ריקים.** בלי "חסרים לך פרטים", בלי progress bar של השלמת פרופיל, בלי אייקון אזהרה ליד אירוע בלי שנה. שדה ריק הוא בחירה לגיטימית של המשתמש.
16. **ברירת מחדל טובה עדיפה על שאלה.** אם יש תשובה שנכונה ל‑90% — קבע אותה בשקט ואפשר לשנות בהגדרות, במקום לשאול את כולם.

---

## 30. Design Rules

### לקסיקון אימוג'ים (מחייב, עקבי בכל המערכת)
| אימוג'י | משמעות | | אימוג'י | משמעות |
|---------|--------|---|---------|--------|
| 🎂 | יום הולדת | | ⚙️ | הגדרות |
| 💍 | יום נישואין | | 📊 | סטטיסטיקות |
| 💒 | חתונה | | 💾 | גיבוי |
| 🕯 | אזכרה | | 📤 | ייצוא/שיתוף |
| 📌 | אירוע מותאם | | 📥 | ייבוא |
| 🎁 | תזכורת מוקדמת | | ✏️ | עריכה |
| 🥳 | שבוע לפני | | 🗑 | מחיקה |
| 📅 | תאריך / רשימה | | ↩️ | ביטול פעולה |
| ✡️ | לוח עברי | | ✅ / ⬜ | דלוק / כבוי |
| ⏳ | ספירה לאחור | | ❌ | ביטול / שגיאה |
| 🎈 | גיל | | 😕 | שגיאה רכה |
| 🔔 / 🔕 | התראות / השתקה | | 🏠 | בית |
| 🏷 | קטגוריה | | 🔍 | חיפוש |
| 👤 | אדם / קשר | | 💌 | ברכה |
| 📞 | טלפון | | 🛠 | ניהול |

### מבנה הודעה
```
<אימוג'י> <b>כותרת</b>
                          ← שורה ריקה
<גוף — עד 5 שורות, כל שורה מתחילה באימוג'י או בטקסט>
                          ← שורה ריקה
<i>רמז/הסבר (אופציונלי)</i>
```

### טיפוגרפיה
- `parse_mode=HTML` בכל מקום (לא Markdown — פחות תקלות escaping).
- `<b>` לשמות ולערכים חשובים בלבד. `<i>` לרמזים. `<code>` לטקסט להעתקה.
- אין `<u>`, אין קו חוצה, אין ספויילר.
- אין קווים מפרידים (`———`) — שורה ריקה מספיקה.

### פורמט תאריכים ומספרים
| דבר | פורמט |
|-----|-------|
| תאריך לועזי | `15/03/1990` (לפי הגדרת המשתמש) |
| תאריך עברי | `י״ט באדר תש״ן` — גימטריה מלאה |
| ספירה לאחור | `היום` / `מחר` / `עוד יומיים` / `עוד 5 ימים` / `עוד שבוע` / `עוד חודשיים` |
| גיל | `36` · חסרה שנה → משמיטים את השורה |
| טלפון | `050-1234567` (מפורמט מ‑E.164 לתצוגה ישראלית) |

---

## 31. Performance

**יעד ריאלי:** עד ~5,000 משתמשים ו‑~100,000 אירועים על VPS צנוע (1 vCPU / 1GB). מעבר לזה — מעבר ל‑Postgres (השכבות מוכנות לזה).

| נושא | פתרון |
|------|-------|
| SQLite | WAL + `synchronous=NORMAL` + `busy_timeout` |
| Tick | שאילתה אחת מסוננת לפי `next_occurrence BETWEEN today AND +45d` — לא סורקת את כל הטבלה |
| `next_occurrence` | מחושב מראש ומאונדקס. אף פעם לא מחושב בתוך `WHERE` |
| N+1 | `selectinload` לכללי תזכורת; טעינה קבוצתית ב‑tick |
| דפדוף | 8 בעמוד, `LIMIT/OFFSET` + `COUNT` נפרד (מטומן ל‑60 שניות) |
| שליחה המונית | `AsyncRateLimiter` 20/sec גלובלי, `asyncio.gather` בבאצ'ים של 20 |
| קאשינג | `functools.lru_cache` על המרות עבריות (`to_hebrew`/`to_gregorian`) — פונקציות טהורות, בטוח |
| קבצים | ייצוא נכתב ל‑temp, נשלח, נמחק מיד |
| זיכרון | יעד < 200MB RSS. `MemoryStorage` מנוקה מ‑states ישנים |
| Vacuum | `PRAGMA optimize` יומי + `VACUUM` שבועי |

**מדדים לניטור (`/dbstats`):** משך tick, מספר תזכורות ב‑tick, גודל DB, RSS, uptime, שיעור כישלון.

---

## 32. Testing

**יעד כיסוי:** `core/` = **100%** · `services/` ≥ 80% · כללי ≥ 70%.

### `tests/test_dates_gregorian.py`
- יום הולדת מחר / היום / אתמול (→ שנה הבאה)
- 31/12 ב‑30/12
- 29/02 בשנה מעוברת ולא מעוברת (שתי המדיניויות)
- שנה NULL → אין גיל
- חישוב גיל מדויק ביום עצמו וביום שלפני

### `tests/test_dates_hebrew.py` (הקריטי ביותר)
- אימות מיפוי החודשים מול pyluach
- הלוך‑חזור: גרגוריאני → עברי → גרגוריאני על 3,000 תאריכים אקראיים
- ל׳ חשוון בשנה חסרה ובשנה מלאה
- ל׳ כסלו בשנה חסרה ובשנה מלאה
- אדר בשנה פשוטה → אדר ב׳ בשנה מעוברת (וההפך)
- אדר א׳ / אדר ב׳ מפורשים
- גיל עברי מול גיל לועזי לאותו אדם (הפרש של עד שנה — תקין)
- גימטריה: `5786 → תשפ״ו`, `15 → ט״ו`, `16 → ט״ז` (לא `י״ה`/`י״ו`!)

### `tests/test_reminder_engine.py` (עם `freezegun`)
- כלל יום‑לפני נורה בדיוק פעם אחת
- שני ticks באותה דקה → הודעה אחת (UNIQUE)
- downtime של 3 שעות → נשלח (בתוך grace)
- downtime של 10 שעות → `skipped`
- שני משתמשים ב‑TZ שונים → כל אחד בשעה המקומית שלו
- מעבר שעון קיץ → עדיין 09:00 מקומי
- כלל ספציפי לאירוע גובר על גלובלי
- `notifications_enabled=0` → כלום
- `TelegramForbiddenError` → `bot_blocked_by_user=1`
- שני כללים באותה דקה → הודעה מאוחדת

### שאר
- `test_validators.py` — כל פורמט תאריך, אורכים, טלפונים, קלט זדוני (`<script>`, תווי בקרה)
- `test_event_service.py` — CRUD, soft delete + restore + purge, מגבלת 1000
- `test_backup_service.py` — round‑trip JSON, CSV עם BOM, ייבוא עם שורות שגויות
- `test_formatting.py` — ריבוי בעברית ("יומיים"), RTL
- `test_handlers_smoke.py` — כל callback נענה ולא קורס (mock bot)
- **טסט חוזה הפשטות:** יצירת אירוע עם `first_name` + `month` + `day` בלבד עוברת בכל שכבה (service, DB, רינדור כרטיס, מנוע תזכורות) בלי חריגה ובלי שדה חסר — זה מוודא שאף שדה "אופציונלי" לא הפך בשקט לחובה
- **טסט אבטחה:** משתמש A לא מצליח לגשת ל‑`ev:v:<id>` של משתמש B — טסט לכל handler שמקבל id

### תשתית
`conftest.py`: `sqlite+aiosqlite:///:memory:` עם כל הטבלאות, fixtures `user`, `event`, `bot_mock`, `frozen_time`.
`make test` = `pytest -q --cov=app --cov-report=term-missing`.

---

## 33. Deployment

**יעד:** Ubuntu 22.04/24.04, systemd + venv, בלי Docker.

### `deploy/install.sh` (idempotent)
```bash
#!/usr/bin/env bash
set -euo pipefail

APP_USER=birthly
APP_DIR=/opt/birthly

sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip sqlite3 git

id -u $APP_USER &>/dev/null || sudo useradd -r -s /bin/false -d $APP_DIR $APP_USER
sudo mkdir -p $APP_DIR $APP_DIR/data/{backups,logs}
sudo chown -R $APP_USER:$APP_USER $APP_DIR
sudo chmod 700 $APP_DIR/data

cd $APP_DIR
sudo -u $APP_USER python3.12 -m venv .venv
sudo -u $APP_USER .venv/bin/pip install --upgrade pip
sudo -u $APP_USER .venv/bin/pip install -r requirements.txt

[ -f .env ] || { sudo -u $APP_USER cp .env.example .env; \
  echo "⚠️  ערוך את .env והכנס BOT_TOKEN, ואז הרץ שוב"; exit 1; }
sudo chmod 600 .env

sudo -u $APP_USER .venv/bin/alembic upgrade head

sudo cp deploy/birthly.service /etc/systemd/system/
sudo cp deploy/logrotate.birthly /etc/logrotate.d/birthly
sudo systemctl daemon-reload
sudo systemctl enable --now birthly
sudo systemctl status birthly --no-pager
```

### `deploy/birthly.service`
```ini
[Unit]
Description=Birthly Telegram Bot (בלי פאדיחות)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=birthly
Group=birthly
WorkingDirectory=/opt/birthly
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/birthly/.venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/birthly/data
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

### `deploy/update.sh`
```bash
cd /opt/birthly
sudo -u birthly git pull
sudo -u birthly .venv/bin/pip install -r requirements.txt
sudo -u birthly .venv/bin/alembic upgrade head
sudo systemctl restart birthly
```

### Graceful shutdown
`main.py` תופס SIGTERM/SIGINT → `scheduler.shutdown(wait=True)` → `dp.stop_polling()` → סגירת engine → `bot.session.close()`. חובה כדי לא לאבד תזכורת באמצע שליחה.

### Health
`app_meta.last_tick_at` מתעדכן בכל tick. `/dbstats` מציג אותו. אין endpoint HTTP — אין שרת web.

### פקודות שימושיות
```
journalctl -u birthly -f          # לוגים חיים
systemctl restart birthly
sqlite3 /opt/birthly/data/birthly.db ".backup /tmp/manual.db"
```

---

## 34. Future Ideas

**Phase 2 (הכי קרוב):** תזכורות לתשלומים/חובות · רשימת מתנות לכל אדם (מה קניתי בשנים קודמות) · "מי לא ברכתי" · הצעות AI לברכה מותאמת אישית · ייצוא ל‑`.ics`.

**Phase 3:** סנכרון Google Calendar (דו‑כיווני) · חגים יהודיים ומועדים · תזכורות משותפות למשפחה (קבוצת טלגרם) · Mini App לתצוגת לוח שנה ויזואלית.

**Phase 4:** ייבוא מאנשי קשר · שליחת ברכה אוטומטית ל‑@username בהסכמה · Premium (אם וכאשר) · ריבוי שפות מעבר ל‑he/en.

> **חשוב:** אף אחד מאלה לא נבנה עכשיו, ואין לבנות "תשתית לקראתם" מעבר להפרדת השכבות שכבר מתוארת. הדבר היחיד שכן: מודל `events` כבר גנרי עם `event_type`, מה שהופך את רוב Phase 2 לתוספת נתונים ולא לשכתוב.

---

## 35. Milestones לסוכן המפתח

סדר בנייה מחייב — כל milestone חייב לעבוד ולעבור טסטים לפני המעבר הלאה.

| # | Milestone | Definition of Done |
|---|-----------|--------------------|
| **M0** | שלד | מבנה תיקיות מלא, `config.py` נטען, `main.py` עולה ועונה `/start` עם "היי" |
| **M1** | DB + מיגרציות | כל המודלים, `alembic upgrade head` עובר, seed של תבניות ברכה |
| **M2** | `core/` + טסטים | `dates.py`, `hebcal.py`, `formatting.py`, `validators.py` — **100% כיסוי**. זה השלב הכי חשוב, לא לדלג |
| **M3** | Middlewares + תפריט | 5 המידלוורים, מסך בית, ניווט, i18n עובד עם `he.json` |
| **M4** | CRUD אירועים | הוספה (לועזי + עברי), רשימה עם דפדוף, כרטיס, עריכה, מחיקה + ביטול |
| **M5** | Scheduler + תזכורות | `tick_reminders` מלא, אידמפוטנטיות, grace window, כל טסטי המנוע ירוקים |
| **M6** | חיפוש + סטטיסטיקות + הגדרות | |
| **M7** | ברכות + גיבוי/ייצוא/ייבוא | |
| **M8** | אדמין + לוגים + טיפול בשגיאות גלובלי | |
| **M9** | Deployment | `install.sh` רץ על שרת נקי מאפס עד בוט חי |
| **M10** | ליטוש | כל המחרוזות עברו הגהה, כל מסך נבדק ידנית בנייד, `ruff` ו‑`mypy` נקיים |

**Definition of Done כללי לכל משימה:** קוד + טסטים + מחרוזות ב‑locale + `ruff check` נקי + עדכון README אם נוספה הגדרה.

---

## 36. שאלות פתוחות

### הוכרע — לא לשנות

| # | נושא | ההכרעה |
|---|------|--------|
| 1 | **@username של הבוט** | **`@Birthday_ILBOT`** — לכפתורי `switch_inline_query` ולקישורי שיתוף |
| 3 | **מדיניות אדר** | **אדר ב׳** (`adar_policy=adar_ii`) כברירת מחדל, ניתן לשינוי בהגדרות. נשאר כפי שמתואר בפרק 10 |
| 6 | **תמונות בייצוא** | **לא מיוצאות.** `photo_file_id` מושמט מכל קובץ ייצוא. פירוט: פרק 23 |

### נותר פתוח — יש ברירת מחדל מחייבת, אפשר להתחיל בלי תשובה

| # | שאלה | ברירת המחדל המחייבת |
|---|------|--------------------|
| 2 | **אזכרות** — האם `memorial` נכנס ל‑V1? הוא מחייב ניסוח מכבד נפרד וביטול ברכות/אימוג'ים חגיגיים. | כן, נכנס — עם טיפול מיוחד |
| 4 | **סל מחזור 30 יום** — מקובל, או שמחיקה = מחיקה מיידית? | 30 יום + `↩️ בטל` |
| 5 | **סיכום יומי** — דלוק או כבוי כברירת מחדל למשתמש חדש? | כבוי (למנוע תחושת ספאם) |
| 7 | **תזכורת "שעתיים לפני"** — יש לה משמעות רק אם הוזנה שעת לידה/אירוע. להשאיר את היכולת או להוריד לפשטות? | להשאיר, מוצגת רק כשיש שעה |
| 8 | **אנגלית** — לתרגם את `en.json` במלואו ב‑V1, או להשאיר שלד ולמלא בהמשך? | שלד מלא + תרגום מלא ב‑M10 |
| 9 | **התראה לאדמין על כל שגיאה** — עלול להציף. לקבץ ולשלוח סיכום כל שעה? | דיווח מיידי + דדופליקציה: אותה שגיאה מדווחת פעם בשעה |
| 10 | **מגבלת 1000 אירועים למשתמש** — הגיוני, או להוריד/להעלות? | 1000 |

---

## 37. Verification

איך לוודא שהמערכת עובדת אחרי הבנייה (end‑to‑end, בסדר הזה):

1. `make lint && make test` — ruff, mypy ו‑pytest ירוקים; כיסוי `core/` = 100%.
2. `alembic upgrade head` על DB ריק ואז `alembic downgrade base` — מיגרציות הפיכות.
3. הרצה מקומית עם טוקן של בוט בדיקה: `/start` → אונבורדינג מלא → הוספת אירוע לועזי → הוספת אירוע עברי → כרטיס → עריכה → מחיקה → שחזור.
3א. **בדיקת חוזה הפשטות (פרק 11.1)** — ספירה בפועל, לא הערכה:
   - הוספת אירוע לועזי מ‑`[➕ הוסף]` עד "נשמר" = **2 מסכים בדיוק**.
   - הוספת תזכורת מ‑`[➕ הוסף תזכורת]` עד "נוסף" = **לחיצה אחת**.
   - לעבור על כל מסך בבוט ולוודא שאין ולו מסך אחד — חוץ משם ותאריך — שאי אפשר להתקדם ממנו בלי למלא.
   - להוסיף אירוע עם שם ותאריך בלבד ולוודא שהבוט לא מזכיר את השדות החסרים באף מסך.
4. **בדיקת תזכורת אמיתית:** להוסיף אירוע להיום, לקבוע כלל `offset_days=0` עם `send_time` שתי דקות קדימה, ולוודא שההודעה מגיעה פעם אחת בלבד. להפעיל את ה‑tick שוב ידנית ולוודא שלא נשלחה שנייה.
5. **בדיקת downtime:** לעצור את התהליך, להזיז שעון מערכת שעתיים, להריץ — התזכורת שפוספסה נשלחת. לחזור על זה עם 10 שעות — היא מסומנת `skipped`.
6. ייצוא JSON → מחיקת החשבון → ייבוא מהקובץ → כל הנתונים חזרו זהים.
7. **בדיקת בידוד:** שני חשבונות טלגרם; לנסות `ev:v:<id>` של האחר → "הפריט לא נמצא", ו‑WARNING בלוג.
8. `bash deploy/install.sh` על VPS נקי → `systemctl status birthly` פעיל → `journalctl -u birthly -f` נקי משגיאות → הבוט עונה בטלגרם.
9. `systemctl restart birthly` תוך כדי המתנה לתזכורת → התזכורת עדיין נשלחת (פעם אחת).
