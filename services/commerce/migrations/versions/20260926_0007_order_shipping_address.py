"""order shipping address: where the order was sent, as a purchase-time snapshot

Revision ID: 4b8e2f6a1d93
Revises: 7d3e9b41c2a8
Create Date: 2026-09-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "4b8e2f6a1d93"
down_revision: str | None = "7d3e9b41c2a8"
branch_labels = None
depends_on = None

COLUMNS = (
    "ship_to_name",
    "ship_to_line1",
    "ship_to_line2",
    "ship_to_city",
    "ship_to_state",
    "ship_to_postal_code",
    "ship_to_country",
    "ship_to_is_sample",
)


def upgrade() -> None:
    # Nullable: an order placed for store pickup (or one created before this column) has none.
    op.add_column("orders", sa.Column("ship_to_name", sa.String(120), nullable=True))
    op.add_column("orders", sa.Column("ship_to_line1", sa.String(200), nullable=True))
    op.add_column("orders", sa.Column("ship_to_line2", sa.String(200), nullable=True))
    op.add_column("orders", sa.Column("ship_to_city", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("ship_to_state", sa.String(40), nullable=True))
    op.add_column("orders", sa.Column("ship_to_postal_code", sa.String(20), nullable=True))
    op.add_column("orders", sa.Column("ship_to_country", sa.String(2), nullable=True))
    op.add_column(
        "orders",
        sa.Column("ship_to_is_sample", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    for name in reversed(COLUMNS):
        op.drop_column("orders", name)
