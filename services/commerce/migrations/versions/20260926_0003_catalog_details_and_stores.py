"""catalog details, tags, perishable policy, stores

Revision ID: aff3bd840644
Revises: a41f6e618248
Create Date: 2026-09-26 11:22:05.783590
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "aff3bd840644"
down_revision: str | None = "a41f6e618248"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fresh and frozen food: refunded without a return shipment (see PRODUCT_REQUIREMENTS.md).
    op.execute("ALTER TYPE policy_class ADD VALUE IF NOT EXISTS 'perishable'")

    op.create_table(
        "stores",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address_line1", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("postal_code", sa.String(length=10), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("hours", sa.JSON(), nullable=False),
        sa.Column("services", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stores")),
        sa.UniqueConstraint("code", name=op.f("uq_stores_code")),
    )
    # Server defaults fill existing rows; the seed sets real values.
    op.add_column(
        "products",
        sa.Column("product_type", sa.String(length=80), nullable=False, server_default="general"),
    )
    op.add_column(
        "products",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String(length=40)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
    )
    op.add_column(
        "products",
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.create_index(op.f("ix_products_product_type"), "products", ["product_type"], unique=False)
    op.create_index("ix_products_tags", "products", ["tags"], unique=False, postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_products_tags", table_name="products", postgresql_using="gin")
    op.drop_index(op.f("ix_products_product_type"), table_name="products")
    op.drop_column("products", "details")
    op.drop_column("products", "tags")
    op.drop_column("products", "product_type")
    op.drop_table("stores")
    # PostgreSQL can't drop an enum value; 'perishable' stays in policy_class.
