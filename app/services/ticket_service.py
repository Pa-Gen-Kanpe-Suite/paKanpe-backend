from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    AuditLog,
    Counter,
    CounterStatus,
    NotificationType,
    Service,
    Ticket,
    TicketSource,
    TicketStatus,
    User,
)
from app.services.notification_service import add_notification, notify_upcoming

ACTIVE_STATUSES = [
    TicketStatus.WAITING.value,
    TicketStatus.CALLED.value,
    TicketStatus.IN_PROGRESS.value,
]


def audit(db: Session, actor_id: int | None, action: str, entity: Ticket | Counter) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity.__class__.__name__,
            entity_id=str(entity.id),
        )
    )


def require_service(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if service is None or not service.is_active:
        raise HTTPException(status_code=404, detail="Service introuvable ou indisponible")
    return service


def create_ticket(
    db: Session,
    service_id: int,
    source: TicketSource,
    actor: User,
    client: User | None = None,
    visitor_name: str | None = None,
    visitor_phone: str | None = None,
) -> Ticket:
    service = require_service(db, service_id)
    if client:
        existing = db.scalar(
            select(Ticket.id).where(
                Ticket.client_id == client.id,
                Ticket.status.in_(ACTIVE_STATUSES),
            )
        )
        if existing:
            raise HTTPException(status_code=409, detail="Ce client possède déjà un ticket actif")
    ticket = Ticket(
        bank_id=service.bank_id,
        client_id=client.id if client else None,
        service_id=service.id,
        source=source.value,
        status=TicketStatus.WAITING.value,
        visitor_name=visitor_name,
        visitor_phone=visitor_phone,
    )
    db.add(ticket)
    try:
        db.flush()
        ticket.code = f"A{ticket.id:04d}"
        add_notification(db, ticket, NotificationType.CREATED)
        notify_upcoming(db)
        audit(db, actor.id, "ticket.created", ticket)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Un ticket actif existe déjà") from exc
    db.refresh(ticket)
    return ticket


def cancel_ticket(db: Session, ticket: Ticket, user: User) -> Ticket:
    if ticket.client_id != user.id:
        raise HTTPException(status_code=403, detail="Ce ticket ne vous appartient pas")
    if ticket.status != TicketStatus.WAITING.value:
        raise HTTPException(status_code=409, detail="Seul un ticket en attente peut être annulé")
    ticket.status = TicketStatus.CANCELLED.value
    ticket.closed_at = datetime.now(UTC)
    add_notification(db, ticket, NotificationType.CANCELLED)
    notify_upcoming(db)
    audit(db, user.id, "ticket.cancelled", ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def current_counter_ticket(db: Session, counter_id: int) -> Ticket | None:
    return db.scalar(
        select(Ticket).where(
            Ticket.counter_id == counter_id,
            Ticket.status.in_([TicketStatus.CALLED.value, TicketStatus.IN_PROGRESS.value]),
        )
    )


def call_next_ticket(db: Session, counter: Counter, cashier: User) -> Ticket:
    if counter.status != CounterStatus.OPEN.value:
        raise HTTPException(status_code=409, detail="Le guichet doit être ouvert")
    if counter.cashier_id not in {None, cashier.id}:
        raise HTTPException(status_code=403, detail="Ce guichet est affecté à un autre caissier")
    if current_counter_ticket(db, counter.id):
        raise HTTPException(
            status_code=409, detail="Terminez le ticket actif avant d'en appeler un autre"
        )
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.status == TicketStatus.WAITING.value)
        .order_by(Ticket.created_at, Ticket.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Aucun ticket en attente")
    ticket.status = TicketStatus.CALLED.value
    ticket.counter_id = counter.id
    ticket.called_at = datetime.now(UTC)
    counter.cashier_id = cashier.id
    add_notification(db, ticket, NotificationType.CALLED, counter=counter.name)
    notify_upcoming(db)
    audit(db, cashier.id, "ticket.called", ticket)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Le ticket vient d'être appelé ailleurs"
        ) from exc
    db.refresh(ticket)
    return ticket


def start_ticket(db: Session, ticket: Ticket, cashier: User) -> Ticket:
    if ticket.status != TicketStatus.CALLED.value:
        raise HTTPException(status_code=409, detail="Le ticket doit être appelé avant le service")
    if ticket.counter is None or ticket.counter.cashier_id != cashier.id:
        raise HTTPException(status_code=403, detail="Ticket affecté à un autre guichet")
    ticket.status = TicketStatus.IN_PROGRESS.value
    ticket.started_at = datetime.now(UTC)
    audit(db, cashier.id, "ticket.started", ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def close_ticket(db: Session, ticket: Ticket, cashier: User, comment: str | None) -> Ticket:
    if ticket.status != TicketStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=409, detail="Le ticket doit être en service")
    if ticket.counter is None or ticket.counter.cashier_id != cashier.id:
        raise HTTPException(status_code=403, detail="Ticket affecté à un autre guichet")
    ticket.status = TicketStatus.CLOSED.value
    ticket.closed_at = datetime.now(UTC)
    ticket.comment = comment
    add_notification(db, ticket, NotificationType.COMPLETED)
    notify_upcoming(db)
    audit(db, cashier.id, "ticket.closed", ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def mark_absent(db: Session, ticket: Ticket, cashier: User) -> Ticket:
    if ticket.status != TicketStatus.CALLED.value or ticket.called_at is None:
        raise HTTPException(status_code=409, detail="Seul un ticket appelé peut être marqué absent")
    if ticket.counter is None or ticket.counter.cashier_id != cashier.id:
        raise HTTPException(status_code=403, detail="Ticket affecté à un autre guichet")
    called_at = ticket.called_at
    if called_at.tzinfo is None:
        called_at = called_at.replace(tzinfo=UTC)
    elapsed = (datetime.now(UTC) - called_at).total_seconds()
    remaining = get_settings().no_show_grace_seconds - elapsed
    if remaining > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Délai de grâce actif pendant encore {int(remaining)} secondes",
        )
    ticket.status = TicketStatus.ABSENT.value
    ticket.closed_at = datetime.now(UTC)
    add_notification(db, ticket, NotificationType.ABSENT)
    notify_upcoming(db)
    audit(db, cashier.id, "ticket.absent", ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
