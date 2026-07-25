from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import Notification, User
from app.schemas import Message, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.sent_at.desc()).limit(50)
    ).all()


@router.patch("/{notification_id}/read", response_model=Message)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    notification.is_read = True
    db.commit()
    return Message(message="Notification lue")
