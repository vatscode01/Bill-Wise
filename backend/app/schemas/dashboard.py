import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StatCard(BaseModel):
    """One dashboard tile: an amount plus how many records made it up."""
    amount: Decimal
    currency: str
    count: int


class UpcomingPayment(BaseModel):
    id: uuid.UUID
    provider: str
    amount: Decimal
    currency: str
    due_date: date
    status: str

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    upcoming: StatCard
    overdue: StatCard
    paid_this_month: StatCard
    recurring_monthly: StatCard
    upcoming_payments: list[UpcomingPayment]


class MonthlySpendPoint(BaseModel):
    month: str  # "YYYY-MM"
    amount: Decimal


class ProviderSpend(BaseModel):
    provider: str
    amount: Decimal


class DashboardCharts(BaseModel):
    currency: str
    monthly_spending: list[MonthlySpendPoint]
    spending_by_provider: list[ProviderSpend]
