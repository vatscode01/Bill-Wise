"""
core/email.py — Email delivery using fastapi-mail.

All templates are plain HTML strings here so we don't need a templates/
directory. For a production app you'd move these to Jinja2 templates.
"""
from __future__ import annotations

import logging
from typing import List

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=bool(settings.mail_username),
        VALIDATE_CERTS=True,
    )


async def send_bill_reminder(
    recipient_email: str,
    provider: str,
    amount: str,
    currency: str,
    due_date: str,
    days_left: int,
) -> None:
    """Send a bill reminder email to a single recipient."""
    if not settings.mail_username:
        logger.warning(
            "MAIL_USERNAME not configured — skipping reminder email for %s",
            recipient_email,
        )
        return

    subject = f"⏰ Reminder: {provider} bill due in {days_left} day(s)"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; padding: 24px;">
      <h2 style="color: #4f46e5;">BillWise Reminder</h2>
      <p>Hi there,</p>
      <p>This is a friendly reminder that your <strong>{provider}</strong> bill is due in
         <strong>{days_left} day(s)</strong>.</p>
      <table style="border-collapse: collapse; width: 100%; margin: 24px 0;">
        <tr>
          <td style="padding: 8px; border: 1px solid #e2e8f0; background:#f8fafc; font-weight:bold;">Provider</td>
          <td style="padding: 8px; border: 1px solid #e2e8f0;">{provider}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #e2e8f0; background:#f8fafc; font-weight:bold;">Amount</td>
          <td style="padding: 8px; border: 1px solid #e2e8f0;">{currency} {amount}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #e2e8f0; background:#f8fafc; font-weight:bold;">Due Date</td>
          <td style="padding: 8px; border: 1px solid #e2e8f0;">{due_date}</td>
        </tr>
      </table>
      <p>Log in to <a href="http://localhost:3000/bills" style="color: #4f46e5;">BillWise</a> to mark it paid.</p>
      <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
      <p style="font-size: 12px; color: #94a3b8;">You received this because you have an active BillWise account.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[recipient_email],
        body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(_get_mail_config())
    try:
        await fm.send_message(message)
        logger.info("Reminder sent to %s for %s", recipient_email, provider)
    except Exception as exc:
        logger.error("Failed to send reminder email to %s: %s", recipient_email, exc)
