from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models import TicketSource, User, UserRole
from app.schemas import PhysicalTicketCreate, TicketOut
from app.services.queue_service import serialize_ticket
from app.services.ticket_service import create_ticket

router = APIRouter(prefix="/agent", tags=["Agent d'accueil"])


@router.post("/tickets/physical", response_model=TicketOut, status_code=201)
def create_physical_ticket(
    payload: PhysicalTicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    ticket = create_ticket(
        db,
        payload.service_id,
        TicketSource.PHYSICAL,
        user,
        visitor_name=payload.visitor_name,
        visitor_phone=payload.visitor_phone,
    )
    return serialize_ticket(db, ticket)
