from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a requested entity doesn't exist or doesn't belong to the caller."""


class LimitError(Exception):
    """Raised when a user-facing quota (events, reminder rules, templates, ...) is exceeded."""
