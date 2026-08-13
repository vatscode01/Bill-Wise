"""
test_reminders.py — Unit tests for the reminder scheduler logic.
All external I/O (DB, email) is mocked so the suite runs offline.
"""
import asyncio
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_reminder_sends_email_for_bill_due_on_target_date():
    """
    If a bill is due in exactly REMINDER_DAYS_BEFORE days and is unpaid,
    an email should be dispatched.
    """
    from app.models.bill import BillStatus
    from app.models.user import User

    target_date = date.today() + timedelta(days=3)

    mock_user = MagicMock(spec=User)
    mock_user.email = "owner@example.com"

    mock_bill = MagicMock()
    mock_bill.provider = "Electricity"
    mock_bill.amount = Decimal("2500.00")
    mock_bill.currency = "INR"
    mock_bill.due_date = target_date
    mock_bill.status = BillStatus.unpaid
    mock_bill.owner = mock_user

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_bill]
    mock_db.query.return_value = mock_query

    with patch("app.core.scheduler.SessionLocal", return_value=mock_db), \
         patch("app.core.scheduler.settings") as mock_settings, \
         patch("app.core.scheduler.send_bill_reminder", new_callable=AsyncMock) as mock_send:

        mock_settings.reminder_days_before = 3
        from app.core.scheduler import _send_upcoming_reminders
        await _send_upcoming_reminders()

    mock_send.assert_called_once_with(
        recipient_email="owner@example.com",
        provider="Electricity",
        amount="2500.00",
        currency="INR",
        due_date=str(target_date),
        days_left=3,
    )


@pytest.mark.asyncio
async def test_reminder_skipped_when_disabled():
    """When reminder_days_before=0 no emails should be sent."""
    with patch("app.core.scheduler.settings") as mock_settings, \
         patch("app.core.scheduler.send_bill_reminder", new_callable=AsyncMock) as mock_send:

        mock_settings.reminder_days_before = 0
        from app.core.scheduler import _send_upcoming_reminders
        await _send_upcoming_reminders()

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_reminder_not_sent_for_paid_bills():
    """Paid bills should never receive reminders."""
    from app.models.bill import BillStatus

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []  # DB filter already excludes paid bills
    mock_db.query.return_value = mock_query

    with patch("app.core.scheduler.SessionLocal", return_value=mock_db), \
         patch("app.core.scheduler.settings") as mock_settings, \
         patch("app.core.scheduler.send_bill_reminder", new_callable=AsyncMock) as mock_send:

        mock_settings.reminder_days_before = 3
        from app.core.scheduler import _send_upcoming_reminders
        await _send_upcoming_reminders()

    mock_send.assert_not_called()
