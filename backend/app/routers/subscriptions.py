import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _get_owned_subscription_or_404(sub_id: uuid.UUID, user: User, db: Session) -> Subscription:
    """Same ownership pattern as bills.py: 404 (not 403) for someone else's subscription."""
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.user_id == user.id).first()
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    sub = Subscription(user_id=user.id, **payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    status_filter: SubscriptionStatus | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GET /subscriptions means 'give me MY subscriptions' — always scoped to the user."""
    query = db.query(Subscription).filter(Subscription.user_id == user.id)
    if status_filter is not None:
        query = query.filter(Subscription.status == status_filter)
    return query.order_by(Subscription.next_renewal.asc()).all()


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_subscription_or_404(sub_id, user, db)


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(
    sub_id: uuid.UUID,
    payload: SubscriptionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = _get_owned_subscription_or_404(sub_id, user, db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(sub, field, value)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(sub_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = _get_owned_subscription_or_404(sub_id, user, db)
    db.delete(sub)
    db.commit()
    return None
