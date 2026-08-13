from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal

class ExtractedBillData(BaseModel):
    provider: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    due_date: Optional[date] = None
    billing_period: Optional[str] = None
