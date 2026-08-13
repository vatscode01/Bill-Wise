from collections import Counter
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.bill import Bill, BillStatus
from app.models.subscription import Subscription, BillingCycle, SubscriptionStatus
from app.models.user import User
from app.schemas.dashboard import (
    StatCard,
    UpcomingPayment,
    DashboardStats,
    MonthlySpendPoint,
    ProviderSpend,
    DashboardCharts,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MONTHS_OF_HISTORY = 6
TOP_PROVIDERS = 5
UPCOMING_PAYMENTS_LIMIT = 5


def _primary_currency(user: User, db: Session) -> str:
    """
    BillWise (v1) assumes a user mostly bills in one currency, same as the
    rest of the dashboard math below. We pick whichever currency shows up
    most often across their bills, defaulting to INR for a brand-new user.
    Real multi-currency support (converting/aggregating across currencies)
    is listed as a Future Improvement, not a Week 4 goal.
    """
    rows = db.query(Bill.currency).filter(Bill.user_id == user.id).all()
    if not rows:
        return "INR"
    counts = Counter(r[0] for r in rows)
    return counts.most_common(1)[0][0]


@router.get("/stats", response_model=DashboardStats)
def get_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    currency = _primary_currency(user, db)

    def _sum_and_count(query):
        amount = query.with_entities(func.coalesce(func.sum(Bill.amount), 0)).scalar()
        count = query.with_entities(func.count(Bill.id)).scalar()
        return Decimal(amount or 0), int(count or 0)

    base = db.query(Bill).filter(Bill.user_id == user.id)

    upcoming_amount, upcoming_count = _sum_and_count(
        base.filter(Bill.status == BillStatus.unpaid, Bill.due_date >= today)
    )
    overdue_amount, overdue_count = _sum_and_count(
        base.filter(Bill.status == BillStatus.unpaid, Bill.due_date < today)
    )
    paid_amount, paid_count = _sum_and_count(
        base.filter(
            Bill.status == BillStatus.paid,
            extract("year", Bill.due_date) == today.year,
            extract("month", Bill.due_date) == today.month,
        )
    )

    # Recurring monthly spend: normalize yearly subscriptions down to a monthly figure
    # so "Netflix (yearly)" and "Spotify (monthly)" can be added together meaningfully.
    active_subs = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == SubscriptionStatus.active)
        .all()
    )
    recurring_amount = Decimal(0)
    for sub in active_subs:
        monthly_equivalent = sub.amount if sub.billing_cycle == BillingCycle.monthly else sub.amount / Decimal(12)
        recurring_amount += monthly_equivalent

    upcoming_payments = (
        base.filter(Bill.status == BillStatus.unpaid, Bill.due_date >= today)
        .order_by(Bill.due_date.asc())
        .limit(UPCOMING_PAYMENTS_LIMIT)
        .all()
    )

    return DashboardStats(
        upcoming=StatCard(amount=upcoming_amount, currency=currency, count=upcoming_count),
        overdue=StatCard(amount=overdue_amount, currency=currency, count=overdue_count),
        paid_this_month=StatCard(amount=paid_amount, currency=currency, count=paid_count),
        recurring_monthly=StatCard(amount=recurring_amount, currency=currency, count=len(active_subs)),
        upcoming_payments=[UpcomingPayment.model_validate(b) for b in upcoming_payments],
    )


@router.get("/charts", response_model=DashboardCharts)
def get_charts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    currency = _primary_currency(user, db)

    # --- Monthly spending (paid bills, last 6 months, oldest -> newest) ---
    # Build the month labels first so months with zero spending still show up
    # on the chart instead of silently disappearing.
    month_starts = [
        (today.replace(day=1) - relativedelta(months=offset)) for offset in range(MONTHS_OF_HISTORY - 1, -1, -1)
    ]
    totals_by_month: dict[str, Decimal] = {m.strftime("%Y-%m"): Decimal(0) for m in month_starts}

    earliest = month_starts[0]
    paid_rows = (
        db.query(
            extract("year", Bill.due_date).label("y"),
            extract("month", Bill.due_date).label("m"),
            func.sum(Bill.amount).label("total"),
        )
        .filter(Bill.user_id == user.id, Bill.status == BillStatus.paid, Bill.due_date >= earliest)
        .group_by("y", "m")
        .all()
    )
    for row in paid_rows:
        key = f"{int(row.y):04d}-{int(row.m):02d}"
        if key in totals_by_month:
            totals_by_month[key] = Decimal(row.total or 0)

    monthly_spending = [MonthlySpendPoint(month=key, amount=amount) for key, amount in totals_by_month.items()]

    # --- Spending by provider (paid bills, top N providers) ---
    provider_rows = (
        db.query(Bill.provider, func.sum(Bill.amount).label("total"))
        .filter(Bill.user_id == user.id, Bill.status == BillStatus.paid)
        .group_by(Bill.provider)
        .order_by(func.sum(Bill.amount).desc())
        .limit(TOP_PROVIDERS)
        .all()
    )
    spending_by_provider = [ProviderSpend(provider=p, amount=Decimal(total or 0)) for p, total in provider_rows]

    return DashboardCharts(
        currency=currency,
        monthly_spending=monthly_spending,
        spending_by_provider=spending_by_provider,
    )
