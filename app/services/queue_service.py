import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Counter, CounterStatus, Service, Ticket, TicketStatus
from app.schemas import DisplayBoard, DisplayTicket, QueuePosition, TicketOut


def active_counter_count(db: Session) -> int:
    return db.scalar(select(func.count(Counter.id)).where(Counter.status == CounterStatus.OPEN.value)) or 0


def average_service_minutes(db: Session) -> float:
    tickets = db.scalars(
        select(Ticket)
        .where(
            Ticket.status == TicketStatus.CLOSED.value,
            Ticket.started_at.is_not(None),
            Ticket.closed_at.is_not(None),
        )
        .order_by(Ticket.closed_at.desc())
        .limit(20)
    ).all()
    durations = [
        max((ticket.closed_at - ticket.started_at).total_seconds() / 60, 0.1)
        for ticket in tickets
        if ticket.closed_at and ticket.started_at
    ]
    if not durations:
        return float(get_settings().default_service_minutes)
    return round(sum(durations) / len(durations), 2)


def position_for_ticket(db: Session, ticket: Ticket) -> int | None:
    if ticket.status in {TicketStatus.CALLED.value, TicketStatus.IN_PROGRESS.value}:
        return 0
    if ticket.status != TicketStatus.WAITING.value:
        return None
    ahead = (
        db.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.status == TicketStatus.WAITING.value,
                or_(
                    Ticket.created_at < ticket.created_at,
                    and_(Ticket.created_at == ticket.created_at, Ticket.id < ticket.id),
                ),
            )
        )
        or 0
    )
    return ahead + 1


def serialize_ticket(db: Session, ticket: Ticket) -> TicketOut:
    position = position_for_ticket(db, ticket)
    counters = max(active_counter_count(db), 1)
    average = average_service_minutes(db)
    wait = None
    if position is not None:
        wait = 0 if position == 0 else math.ceil(max(position - 1, 0) * average / counters)
    service = ticket.service or db.get(Service, ticket.service_id)
    counter_name = ticket.counter.name if ticket.counter else None
    return TicketOut(
        id=ticket.id,
        code=ticket.code or f"A{ticket.id:04d}",
        source=ticket.source,
        status=ticket.status,
        service_id=ticket.service_id,
        service_name=service.name,
        counter_id=ticket.counter_id,
        counter_name=counter_name,
        visitor_name=ticket.visitor_name,
        position=position,
        estimated_wait_minutes=wait,
        created_at=ticket.created_at,
        called_at=ticket.called_at,
        started_at=ticket.started_at,
        closed_at=ticket.closed_at,
        comment=ticket.comment,
    )


def queue_position(db: Session, ticket: Ticket) -> QueuePosition:
    current_code = db.scalar(
        select(Ticket.code)
        .where(Ticket.status.in_([TicketStatus.CALLED.value, TicketStatus.IN_PROGRESS.value]))
        .order_by(Ticket.called_at.desc())
        .limit(1)
    )
    return QueuePosition(
        ticket=serialize_ticket(db, ticket),
        current_called_code=current_code,
        active_counters=active_counter_count(db),
        average_service_minutes=average_service_minutes(db),
    )


def display_board(db: Session) -> DisplayBoard:
    since = datetime.now(UTC) - timedelta(hours=12)
    called = db.scalars(
        select(Ticket)
        .where(
            Ticket.status.in_([TicketStatus.CALLED.value, TicketStatus.IN_PROGRESS.value]),
            Ticket.called_at >= since,
        )
        .order_by(Ticket.called_at.desc())
        .limit(8)
    ).all()
    waiting = db.scalar(select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.WAITING.value)) or 0
    return DisplayBoard(
        called=[
            DisplayTicket(
                code=ticket.code or f"A{ticket.id:04d}",
                counter_name=ticket.counter.name if ticket.counter else "Guichet",
                called_at=ticket.called_at,
            )
            for ticket in called
            if ticket.called_at
        ],
        waiting_count=waiting,
        updated_at=datetime.now(UTC),
    )
