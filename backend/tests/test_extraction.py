"""
test_extraction.py — Tests for the POST /bills/extract endpoint.
The OpenAI call is mocked so tests never hit the real API.
"""
from unittest.mock import patch, MagicMock
from decimal import Decimal
import io


MOCK_EXTRACTED = {
    "provider": "BSES Rajdhani Power Ltd",
    "amount": 1234.56,
    "currency": "INR",
    "due_date": "2026-09-15",
    "billing_period": "monthly",
}


def _make_fake_pdf_bytes() -> bytes:
    """Minimal valid bytes that look like a PDF to pdfplumber (it will fail gracefully)."""
    return b"%PDF-1.4 fake content"


def test_extract_bill_requires_auth(client):
    fake_pdf = io.BytesIO(b"%PDF fake")
    r = client.post(
        "/bills/extract",
        files={"file": ("bill.pdf", fake_pdf, "application/pdf")},
    )
    assert r.status_code == 401


def test_extract_bill_rejects_unsupported_type(client, auth_headers):
    headers = auth_headers()
    r = client.post(
        "/bills/extract",
        files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
        headers=headers,
    )
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_extract_bill_with_mocked_ai(client, auth_headers):
    """
    Upload a fake PDF. We mock:
      1. pdfplumber text extraction — returns dummy bill text.
      2. OpenAI structured output call — returns MOCK_EXTRACTED.
    """
    headers = auth_headers()

    with patch("app.core.document.pdfplumber") as mock_plumber, \
         patch("app.core.ai.extract_bill_data_from_text") as mock_ai:

        # Simulate pdfplumber returning text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "BSES Rajdhani Power Ltd\nAmount: 1234.56\nDue: 2026-09-15"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value = mock_pdf

        # Simulate AI returning structured data
        from app.schemas.extraction import ExtractedBillData
        mock_ai.return_value = ExtractedBillData(
            provider="BSES Rajdhani Power Ltd",
            amount=Decimal("1234.56"),
            currency="INR",
            due_date="2026-09-15",
            billing_period="monthly",
        )

        fake_pdf = io.BytesIO(b"%PDF fake")
        r = client.post(
            "/bills/extract",
            files={"file": ("bill.pdf", fake_pdf, "application/pdf")},
            headers=headers,
        )

    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "BSES Rajdhani Power Ltd"
    assert float(body["amount"]) == pytest.approx(1234.56, abs=0.01)
    assert body["currency"] == "INR"


def test_extract_image_bill_with_mocked_ai(client, auth_headers):
    """Upload a fake JPEG; verify Vision path is called (mocked)."""
    headers = auth_headers()

    with patch("app.core.document.encode_image_to_base64") as mock_encode, \
         patch("app.core.ai.extract_bill_data_from_image") as mock_ai:

        mock_encode.return_value = "base64encodedimage"
        from app.schemas.extraction import ExtractedBillData
        mock_ai.return_value = ExtractedBillData(
            provider="Airtel",
            amount=Decimal("499.00"),
            currency="INR",
            due_date="2026-09-10",
            billing_period="monthly",
        )

        fake_jpg = io.BytesIO(b"\xff\xd8\xff fake jpeg")
        r = client.post(
            "/bills/extract",
            files={"file": ("receipt.jpg", fake_jpg, "image/jpeg")},
            headers=headers,
        )

    assert r.status_code == 200
    assert r.json()["provider"] == "Airtel"


import pytest
