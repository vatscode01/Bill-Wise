import enum
import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Numeric, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class BillStatus(str, enum.Enum):
    unpaid = "unpaid"
    paid = "paid"
    overdue = "overdue"


class BillingPeriod(str, enum.Enum):
    one_time = "one_time"
    monthly = "monthly"
    yearly = "yearly"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    # Numeric, NOT float — money should never lose precision to floating point rounding.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period: Mapped[BillingPeriod] = mapped_column(
        Enum(BillingPeriod, name="billing_period"), default=BillingPeriod.one_time, nullable=False
    )
    status: Mapped[BillStatus] = mapped_column(
        Enum(BillStatus, name="bill_status"), default=BillStatus.unpaid, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner = relationship("User", back_populates="bills")
