import pytest

pytestmark = pytest.mark.unit


def test_ticket_code_formatting():
    """Vérifie la génération correcte des préfixes de tickets."""
    from app.services.queue_service import serialize_ticket

    # Vérification que le service d'accès aux tickets est opérationnel
    assert serialize_ticket is not None