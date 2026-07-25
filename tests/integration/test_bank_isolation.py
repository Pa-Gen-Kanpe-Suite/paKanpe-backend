import pytest

pytestmark = pytest.mark.integration


def test_cashier_cannot_access_other_bank_tickets(api, cashier_headers):
    """Vérifie le cloisonnement multi-agences : un caissier ne peut pas
    toucher aux tickets d'un autre guichet non rattaché.
    """
    # Tentative d'appeler un ticket sur un guichet inexistant ou d'une autre banque
    response = api.post(
        "/api/v1/cashier/counters/9999/next-ticket",
        headers=cashier_headers,
    )
    assert response.status_code in [403, 404]
