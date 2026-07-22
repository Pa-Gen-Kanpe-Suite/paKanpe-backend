from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models import Counter, CounterStatus, User, UserRole
from app.schemas import CounterCreate, CounterOut, CounterStatusUpdate, StatisticsOverview
from app.services.statistics_service import overview
from app.services.ticket_service import current_counter_ticket

router = APIRouter(prefix="/admin", tags=["Administration"])
admin_only = require_roles(UserRole.ADMIN)


def as_counter_out(db: Session, counter: Counter) -> CounterOut:
    from app.services.queue_service import serialize_ticket

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
def list_counters(db: Session = Depends(get_db), user: User = Depends(admin_only)):
    return [
        as_counter_out(db, counter)
        for counter in db.scalars(select(Counter).order_by(Counter.number)).all()
    ]


@router.post("/counters", response_model=CounterOut, status_code=201)
def create_counter(
    payload: CounterCreate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    bank_id = user.bank_id or db.scalar(select(Counter.bank_id).limit(1)) or 1
    counter = Counter(
        bank_id=bank_id,
        number=payload.number,
        name=payload.name.strip(),
        status=CounterStatus.CLOSED.value,
    )
    db.add(counter)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce numéro de guichet existe déjà") from exc
    db.refresh(counter)
    return as_counter_out(db, counter)


@router.patch("/counters/{counter_id}/status", response_model=CounterOut)
def set_counter_status(
    counter_id: int,
    payload: CounterStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    counter = db.get(Counter, counter_id)
    if counter is None:
        raise HTTPException(status_code=404, detail="Guichet introuvable")
    if payload.status != CounterStatus.OPEN and current_counter_ticket(db, counter.id):
        raise HTTPException(status_code=409, detail="Un ticket est actif sur ce guichet")
    counter.status = payload.status.value
    if payload.status == CounterStatus.CLOSED:
        counter.cashier_id = None
    db.commit()
    db.refresh(counter)
    return as_counter_out(db, counter)


@router.get("/statistics/overview", response_model=StatisticsOverview)
def statistics(
    selected_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    return overview(db, selected_date)
