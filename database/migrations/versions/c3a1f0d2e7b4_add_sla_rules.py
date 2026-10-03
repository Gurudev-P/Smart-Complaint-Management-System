"""add sla_rules configuration table with default targets

Revision ID: c3a1f0d2e7b4
Revises: bfc7a4ba29c3
Create Date: 2026-10-03 20:00:00

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "c3a1f0d2e7b4"
down_revision: Union[str, Sequence[str], None] = "bfc7a4ba29c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULTS = {"CRITICAL": 240, "HIGH": 1440, "MEDIUM": 4320, "LOW": 10080}


def upgrade() -> None:
    sla_rules = op.create_table(
        "sla_rules",
        sa.Column("rule_id", sa.UUID(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("target_minutes", sa.Integer(), nullable=False),
        sa.Column("approaching_percent", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("rule_id"),
        sa.UniqueConstraint("priority"),
    )
    op.bulk_insert(
        sla_rules,
        [
            {"rule_id": uuid.uuid4(), "priority": p, "target_minutes": m, "approaching_percent": 80}
            for p, m in DEFAULTS.items()
        ],
    )


def downgrade() -> None:
    op.drop_table("sla_rules")
