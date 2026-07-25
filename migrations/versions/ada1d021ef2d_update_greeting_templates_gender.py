"""update_greeting_templates_gender

Revision ID: ada1d021ef2d
Revises: 20c265ea370d
Create Date: 2026-07-25 12:31:38.024040

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'ada1d021ef2d'
down_revision: str | None = '20c265ea370d'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


from app.db.seed_templates import SEED_GREETING_TEMPLATES

def upgrade() -> None:
    # 1. Delete all existing system templates (where user_id IS NULL)
    op.execute("DELETE FROM greeting_templates WHERE user_id IS NULL")
    
    # 2. Insert the updated system templates (now including gender specific variants)
    greeting_templates = sa.table(
        'greeting_templates',
        sa.column('event_type', sa.String()),
        sa.column('tone', sa.String()),
        sa.column('gender', sa.String()),
        sa.column('language', sa.String()),
        sa.column('body', sa.String()),
        sa.column('is_active', sa.Boolean()),
    )
    
    op.bulk_insert(
        greeting_templates,
        [
            {
                "event_type": event_type,
                "tone": tone,
                "gender": gender,
                "language": language,
                "body": body,
                "is_active": True,
            }
            for event_type, tone, gender, language, body in SEED_GREETING_TEMPLATES
        ],
    )


def downgrade() -> None:
    # Downgrade will leave the updated templates as they are (no data loss)
    pass
