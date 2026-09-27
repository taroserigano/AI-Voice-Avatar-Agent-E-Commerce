"""return quotes: exact terms, quote hash, single-use confirmation token (hashed)

Revision ID: 7d3e9b41c2a8
Revises: 02a9f1af65a9
Create Date: 2026-09-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "7d3e9b41c2a8"
down_revision: str | None = "02a9f1af65a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "return_quotes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("lines", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(60), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("shipping_refund_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_refund_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("payment_id", sa.Uuid(), sa.ForeignKey("payment_attempts.id"), nullable=True),
        sa.Column("quote_hash", sa.String(64), nullable=False),
        sa.Column("created_via", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=True),
        sa.Column("token_issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(120), nullable=True),
        sa.Column(
            "return_id", sa.Uuid(), sa.ForeignKey("return_requests.id"), nullable=True, unique=True
        ),
        sa.CheckConstraint("total_refund_minor >= 0", name="ck_return_quotes_total_non_negative"),
    )
    op.create_index("ix_return_quotes_user_id", "return_quotes", ["user_id"])
    op.create_index("ix_return_quotes_order_id", "return_quotes", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_return_quotes_order_id", "return_quotes")
    op.drop_index("ix_return_quotes_user_id", "return_quotes")
    op.drop_table("return_quotes")
