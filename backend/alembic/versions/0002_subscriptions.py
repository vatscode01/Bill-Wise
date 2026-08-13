"""add subscriptions table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    billing_cycle_enum = postgresql.ENUM("monthly", "yearly", name="billing_cycle")
    subscription_status_enum = postgresql.ENUM("active", "cancelled", name="subscription_status")
    billing_cycle_enum.create(op.get_bind(), checkfirst=True)
    subscription_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("billing_cycle", billing_cycle_enum, nullable=False, server_default="monthly"),
        sa.Column("next_renewal", sa.Date, nullable=False),
        sa.Column("status", subscription_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade():
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    postgresql.ENUM(name="subscription_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="billing_cycle").drop(op.get_bind(), checkfirst=True)
