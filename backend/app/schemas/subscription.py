import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.subscription import BillingCycle, SubscriptionStatus


class SubscriptionBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, description="Must be a positive amount")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    billing_cycle: BillingCycle = BillingCycle.monthly
    next_renewal: date

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_cycle: BillingCycle | None = None
    next_renewal: date | None = None
    status: SubscriptionStatus | None = None


class SubscriptionOut(SubscriptionBase):
    id: uuid.UUID
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
