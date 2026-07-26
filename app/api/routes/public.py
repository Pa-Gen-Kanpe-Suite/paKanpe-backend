import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.models import Service, Ticket
from app.schemas import DisplayBoard, QueuePosition, ServiceOut
from app.services.queue_service import display_board, queue_position

router = APIRouter(tags=["Public"])


@router.get("/services", response_model=list[ServiceOut])
def services(db: Session = Depends(get_db)):
    return db.scalars(
        select(Service).where(Service.is_active.is_(True)).order_by(Service.id)
    ).all()


@router.get("/queues/position/{ticket_code}", response_model=QueuePosition)
def position(ticket_code: str, db: Session = Depends(get_db)):
    ticket = db.scalar(select(Ticket).where(Ticket.code == ticket_code.upper()))
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return queue_position(db, ticket)


@router.get("/display", response_model=DisplayBoard)
def display(db: Session = Depends(get_db)):
    return display_board(db)


@router.websocket("/ws/queue")
async def queue_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            with SessionLocal() as db:
                payload = display_board(db).model_dump(mode="json")
            await websocket.send_json(payload)
            await asyncio.sleep(2)
    except (WebSocketDisconnect, RuntimeError):
        return
