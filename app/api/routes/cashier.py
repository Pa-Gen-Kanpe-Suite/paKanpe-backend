from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models import Counter, CounterStatus, Ticket, User, UserRole
from app.schemas import CloseTicketRequest, CounterOut, CounterStatusUpdate, TicketOut
from app.services.queue_service import serialize_ticket
from app.services.ticket_service import (
    call_next_ticket,
    close_ticket,
    current_counter_ticket,
    mark_absent,
    start_ticket,
)

router = APIRouter(prefix="/cashier", tags=["Caissier"])
cashier_only = require_roles(UserRole.CASHIER)


def counter_out(db: Session, counter: Counter) -> CounterOut:
    ticket = current_counter_ticket(db, counter.id)
    return CounterOut(
        id=counter.id,
        number=counter.number,
        name=counter.name,
        status=counter.status,
        cashier_id=counter.cashier_id,
        current_ticket=serialize_ticket(db, ticket) if ticket else None,
    )


@router.get("/counters", response_model=list[CounterOut])
def counters(db: Session = Depends(get_db), user: User = Depends(cashier_only)):
    rows = db.scalars(select(Counter).order_by(Counter.number)).all()
    return [counter_out(db, row) for row in rows]


@router.patch("/counters/{counter_id}/status", response_model=CounterOut)
def update_counter_status(
    counter_id: int,
    payload: CounterStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(cashier_only),
):
    counter = db.get(Counter, counter_id)
    if counter is None:
        raise HTTPException(status_code=404, detail="Guichet introuvable")
    if counter.cashier_id not in {None, user.id}:
        raise HTTPException(
            status_code=403, detail="Guichet utilisé par un autre caissier"
        )
    if payload.status != CounterStatus.OPEN and current_counter_ticket(db, counter.id):
        raise HTTPException(
            status_code=409, detail="Terminez le ticket actif avant la pause"
        )
    counter.status = payload.status.value
    counter.cashier_id = user.id if payload.status != CounterStatus.CLOSED else None
    db.commit()
    db.refresh(counter)
    return counter_out(db, counter)


@router.post("/counters/{counter_id}/next-ticket", response_model=TicketOut)
def next_ticket(
    counter_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(cashier_only),
):
    counter = db.get(Counter, counter_id)
    if counter is None:
        raise HTTPException(status_code=404, detail="Guichet introuvable")
    return serialize_ticket(db, call_next_ticket(db, counter, user))


@router.patch("/tickets/{ticket_id}/start", response_model=TicketOut)
def start(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(cashier_only),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return serialize_ticket(db, start_ticket(db, ticket, user))


@router.patch("/tickets/{ticket_id}/close", response_model=CounterOut)
def close(
    ticket_id: int,
    payload: CloseTicketRequest,
    db: Session = Depends(get_db),
    user: User = Depends(cashier_only),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    counter = ticket.counter
    close_ticket(db, ticket, user, payload.comment)
    if (
        payload.auto_call_next
        and counter
        and counter.status == CounterStatus.OPEN.value
    ):
        try:
            call_next_ticket(db, counter, user)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
    return counter_out(db, counter)


@router.patch("/tickets/{ticket_id}/no-show", response_model=TicketOut)
def no_show(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(cashier_only),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return serialize_ticket(db, mark_absent(db, ticket, user))
