from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Bank, Ticket, TicketSource, TicketStatus
from app.services.queue_service import average_service_minutes, position_for_ticket

pytestmark = pytest.mark.unit


def test_position_follows_creation_order(service_id):
    """
    Vérifie que la position attribuée dans la file respecte
    l'ordre chronologique (FIFO).
    """
    with SessionLocal() as db:
        bank_id = db.scalar(select(Bank.id))
        first = Ticket(
            bank_id=bank_id,
            service_id=service_id,
            source=TicketSource.PHYSICAL.value,
            status=TicketStatus.WAITING.value,
            code="A0001",
            visitor_name="Un",
        )
        second = Ticket(
            bank_id=bank_id,
            service_id=service_id,
            source=TicketSource.PHYSICAL.value,
            status=TicketStatus.WAITING.value,
            code="A0002",
            visitor_name="Deux",
        )
        db.add_all([first, second])
        db.commit()

        # Validation du rang
        assert position_for_ticket(db, first) == 1
        assert position_for_ticket(db, second) == 2


def test_average_uses_recent_completed_tickets(service_id):
    """
    Vérifie que la moyenne du temps s'adapte en fonction
    des tickets clôturés (CLOSED).
    """
    with SessionLocal() as db:
        bank_id = db.scalar(select(Bank.id))
        now = datetime.now(UTC)
        ticket = Ticket(
            bank_id=bank_id,
            service_id=service_id,
            source=TicketSource.PHYSICAL.value,
            status=TicketStatus.CLOSED.value,
            code="A0099",
            visitor_name="Terminé",
            started_at=now - timedelta(minutes=8),
            closed_at=now,
        )
        db.add(ticket)
        db.commit()

        # Le calcul de moyenne doit retourner exactement 8 minutes
        assert average_service_minutes(db) == 8