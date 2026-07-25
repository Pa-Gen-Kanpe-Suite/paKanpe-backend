# backend/tests/unit/test_ticket_code.py
import pytest

pytestmark = pytest.mark.unit


def test_ticket_code_formatting():
    """Vérifie la génération correcte des préfixes de tickets."""
    from app.services.ticket_service import generate_ticket_code

    code_depot = generate_ticket_code(service_code="DEPOT", sequence_number=5)
    assert code_depot == "D-005" or "DEP-005" in code_depot
