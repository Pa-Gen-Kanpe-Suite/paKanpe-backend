from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models import Ticket, TicketSource, TicketStatus, User, UserRole
from app.schemas import TicketCreate, TicketOut
from app.services.queue_service import serialize_ticket
from app.services.ticket_service import cancel_ticket, create_ticket

router = APIRouter(prefix="/client", tags=["Client"])
client_only = require_roles(UserRole.CLIENT)


@router.post("/tickets", response_model=TicketOut, status_code=201)
def create_digital_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(client_only),
):
    ticket = create_ticket(db, payload.service_id, TicketSource.DIGITAL, user, client=user)
    return serialize_ticket(db, ticket)


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    user: User = Depends(client_only),
):
    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.client_id == user.id)
        .order_by(Ticket.created_at.desc())
        .limit(50)
    ).all()
    return [serialize_ticket(db, ticket) for ticket in tickets]


@router.get("/tickets/current", response_model=TicketOut | None)
def current_ticket(
    db: Session = Depends(get_db),
    user: User = Depends(client_only),
):
    ticket = db.scalar(
        select(Ticket)
        .where(
            Ticket.client_id == user.id,
            Ticket.status.in_(
                [
                    TicketStatus.WAITING.value,
                    TicketStatus.CALLED.value,
                    TicketStatus.IN_PROGRESS.value,
                ]
            ),
        )
        .order_by(Ticket.created_at.desc())
    )
    return serialize_ticket(db, ticket) if ticket else None


@router.patch("/tickets/{ticket_id}/cancel", response_model=TicketOut)
def cancel(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(client_only),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return serialize_ticket(db, cancel_ticket(db, ticket, user))
