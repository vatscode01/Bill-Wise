import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.bill import BillStatus, BillingPeriod


class BillBase(BaseModel):
    provider: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, description="Must be a positive amount")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    due_date: date
    billing_period: BillingPeriod = BillingPeriod.one_time
    notes: str | None = None

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class BillCreate(BillBase):
    pass


class BillUpdate(BaseModel):
    provider: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    due_date: date | None = None
    billing_period: BillingPeriod | None = None
    status: BillStatus | None = None
    notes: str | None = None


class BillOut(BillBase):
    id: uuid.UUID
    status: BillStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
