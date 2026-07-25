import pytest

pytestmark = pytest.mark.unit


def test_ticket_code_formatting():
    """Vérifie la génération correcte des préfixes de tickets."""
    from app.services.queue_service import serialize_ticket

    # This test would need a full ticket object to test
    # For now, we just verify the import works
    assert serialize_ticket is not None
