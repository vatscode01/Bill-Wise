"""initial schema: users and bills

Revision ID: 0001
Revises:
Create Date: 2026-08-13

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    billing_period_enum = postgresql.ENUM("one_time", "monthly", "yearly", name="billing_period")
    bill_status_enum = postgresql.ENUM("unpaid", "paid", "overdue", name="bill_status")
    billing_period_enum.create(op.get_bind(), checkfirst=True)
    bill_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "bills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("billing_period", billing_period_enum, nullable=False, server_default="one_time"),
        sa.Column("status", bill_status_enum, nullable=False, server_default="unpaid"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bills_user_id", "bills", ["user_id"])


def downgrade():
    op.drop_index("ix_bills_user_id", table_name="bills")
    op.drop_table("bills")
    postgresql.ENUM(name="bill_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="billing_period").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
