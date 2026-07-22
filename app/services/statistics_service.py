from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Counter, CounterStatus, Ticket, TicketStatus
from app.schemas import StatisticsOverview
from app.services.queue_service import average_service_minutes


def overview(db: Session, day: date | None = None) -> StatisticsOverview:
    selected = day or datetime.now(UTC).date()
    start = datetime.combine(selected, time.min, tzinfo=UTC)
    end = datetime.combine(selected, time.max, tzinfo=UTC)

    def count(*statuses: str) -> int:
        return (
            db.scalar(
                select(func.count(Ticket.id)).where(
                    Ticket.created_at.between(start, end), Ticket.status.in_(statuses)
                )
            )
            or 0
        )

    tickets = db.scalars(select(Ticket).where(Ticket.created_at.between(start, end))).all()
    waits = []
    for ticket in tickets:
        if ticket.called_at:
            waits.append(max((ticket.called_at - ticket.created_at).total_seconds() / 60, 0))
    active = (
        db.scalar(select(func.count(Counter.id)).where(Counter.status == CounterStatus.OPEN.value))
        or 0
    )
    return StatisticsOverview(
        date=selected.isoformat(),
        tickets_issued=len(tickets),
        waiting=count(TicketStatus.WAITING.value),
        in_service=count(TicketStatus.CALLED.value, TicketStatus.IN_PROGRESS.value),
        completed=count(TicketStatus.CLOSED.value),
        cancelled=count(TicketStatus.CANCELLED.value),
        absent=count(TicketStatus.ABSENT.value),
        average_wait_minutes=round(sum(waits) / len(waits), 2) if waits else 0,
        average_service_minutes=average_service_minutes(db),
        active_counters=active,
    )
