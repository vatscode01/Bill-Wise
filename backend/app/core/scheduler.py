"""
core/scheduler.py — APScheduler background job that runs every morning
and sends bill-due reminders.

The job is registered on app startup and shut down cleanly on app shutdown
via FastAPI lifespan events.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_bill_reminder
from app.database import SessionLocal
from app.models.bill import Bill, BillStatus

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _send_upcoming_reminders() -> None:
    """
    Runs daily. Queries all unpaid bills whose due_date is exactly
    `reminder_days_before` days from today and sends one email per bill.
    """
    if settings.reminder_days_before <= 0:
        return

    target_date = date.today() + timedelta(days=settings.reminder_days_before)
    db: Session = SessionLocal()
    try:
        bills = (
            db.query(Bill)
            .filter(
                Bill.due_date == target_date,
                Bill.status == BillStatus.unpaid,
            )
            .all()
        )
        logger.info("Reminder job: found %d bill(s) due on %s", len(bills), target_date)
        for bill in bills:
            # Eager-load the owner email via the relationship
            owner = bill.owner
            if owner:
                await send_bill_reminder(
                    recipient_email=owner.email,
                    provider=bill.provider,
                    amount=str(bill.amount),
                    currency=bill.currency,
                    due_date=str(bill.due_date),
                    days_left=settings.reminder_days_before,
                )
    finally:
        db.close()


def start_scheduler() -> None:
    """Register the daily job and start the scheduler. Call on app startup."""
    scheduler.add_job(
        _send_upcoming_reminders,
        trigger="cron",
        hour=8,          # 8 AM server time every day
        minute=0,
        id="daily_bill_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — daily bill reminders enabled.")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler. Call on app shutdown."""
    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down.")
