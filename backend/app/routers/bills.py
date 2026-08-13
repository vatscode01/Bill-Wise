import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.bill import Bill, BillStatus
from app.models.user import User
from app.schemas.bill import BillCreate, BillUpdate, BillOut
from app.schemas.extraction import ExtractedBillData
from app.core.document import extract_text_from_pdf, encode_image_to_base64
from app.core.ai import extract_bill_data_from_text, extract_bill_data_from_image
from fastapi import File, UploadFile
import tempfile
import shutil
import os
router = APIRouter(prefix="/bills", tags=["bills"])


def _get_owned_bill_or_404(bill_id: uuid.UUID, user: User, db: Session) -> Bill:
    """
    Shared ownership check used by GET/PUT/DELETE for a single bill.
    Returns 404 (not 403) for another user's bill, so we don't even reveal
    that the bill exists.
    """
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return bill


@router.post("", response_model=BillOut, status_code=status.HTTP_201_CREATED)
def create_bill(payload: BillCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bill = Bill(user_id=user.id, **payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.get("", response_model=list[BillOut])
def list_bills(
    status_filter: BillStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GET /bills means 'give me MY bills' — always scoped to the authenticated user."""
    query = db.query(Bill).filter(Bill.user_id == user.id)
    if status_filter is not None:
        query = query.filter(Bill.status == status_filter)
    return query.order_by(Bill.due_date.asc()).all()


@router.get("/{bill_id}", response_model=BillOut)
def get_bill(bill_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_bill_or_404(bill_id, user, db)


@router.put("/{bill_id}", response_model=BillOut)
def update_bill(
    bill_id: uuid.UUID,
    payload: BillUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = _get_owned_bill_or_404(bill_id, user, db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(bill, field, value)
    db.commit()
    db.refresh(bill)
    return bill


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bill = _get_owned_bill_or_404(bill_id, user, db)
    db.delete(bill)
    db.commit()
    return None


@router.post("/{bill_id}/mark-paid", response_model=BillOut)
def mark_bill_paid(bill_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bill = _get_owned_bill_or_404(bill_id, user, db)
    bill.status = BillStatus.paid
    db.commit()
    db.refresh(bill)
    return bill


@router.post("/extract", response_model=ExtractedBillData)
def extract_bill(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, JPEG, or PNG.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}" if '.' in file.filename else "") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        if file.content_type == "application/pdf":
            text = extract_text_from_pdf(tmp_path)
            if not text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
            return extract_bill_data_from_text(text)
        else:
            base64_img = encode_image_to_base64(tmp_path)
            return extract_bill_data_from_image(base64_img, mime_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
