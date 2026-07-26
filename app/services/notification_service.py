from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Notification, NotificationType, Ticket

MESSAGES = {
    NotificationType.CREATED: "Votre ticket {code} a été créé.",
    NotificationType.UPCOMING: "Votre tour approche. Préparez-vous à rejoindre l'agence.",
    NotificationType.CALLED: "Le ticket {code} est appelé au {counter}.",
    NotificationType.CANCELLED: "Le ticket {code} a été annulé.",
    NotificationType.ABSENT: "Le ticket {code} a expiré pour absence.",
    NotificationType.COMPLETED: "Le service du ticket {code} est terminé.",
}


def add_notification(
    db: Session,
    ticket: Ticket,
    notification_type: NotificationType,
    counter: str = "guichet",
    unique: bool = False,
) -> None:
    if ticket.client_id is None:
        return
    if unique:
        exists = db.scalar(
            select(Notification.id).where(
                Notification.ticket_id == ticket.id,
                Notification.type == notification_type.value,
            )
        )
        if exists:
            return
    db.add(
        Notification(
            ticket_id=ticket.id,
            user_id=ticket.client_id,
            type=notification_type.value,
            message=MESSAGES[notification_type].format(
                code=ticket.code, counter=counter
            ),
        )
    )


def notify_upcoming(db: Session) -> None:
    from app.models import TicketStatus
    from app.services.queue_service import serialize_ticket

    threshold = get_settings().upcoming_notification_minutes
    waiting = db.scalars(
        select(Ticket)
        .where(
            Ticket.status == TicketStatus.WAITING.value, Ticket.client_id.is_not(None)
        )
        .order_by(Ticket.created_at, Ticket.id)
        .limit(100)
    ).all()
    for ticket in waiting:
        projection = serialize_ticket(db, ticket)
        if (
            projection.estimated_wait_minutes is not None
            and projection.estimated_wait_minutes <= threshold
        ):
            add_notification(db, ticket, NotificationType.UPCOMING, unique=True)
