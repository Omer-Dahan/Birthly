from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.db.models import User


def user_today(user: User) -> date:
    """Today's date in the user's configured timezone (SPEC.md chapter 9)."""
    return datetime.now(ZoneInfo(user.timezone)).date()
