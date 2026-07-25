# backend/tests/integration/test_ticket_rules.py
import pytest

pytestmark = pytest.mark.integration


def test_client_cannot_cancel_called_ticket(api, client_headers, cashier_headers, service_id):
    """Règle métier : Un client ne peut pas annuler son ticket s'il est déjà appelé."""
    # 1. Création du ticket
    ticket = api.post("/api/v1/client/tickets", json={"service_id": service_id}, headers=client_headers).json()

    # 2. Le caissier ouvre et appelle
    counter = api.get("/api/v1/cashier/counters", headers=cashier_headers).json()[0]
    api.patch(
        f"/api/v1/cashier/counters/{counter['id']}/status",
        json={"status": "OPEN"},
        headers=cashier_headers,
    )
    api.post(f"/api/v1/cashier/counters/{counter['id']}/next-ticket", headers=cashier_headers)

    # 3. Le client tente d'annuler -> Refusé
    cancelled = api.patch(f"/api/v1/client/tickets/{ticket['id']}/cancel", headers=client_headers)
    assert cancelled.status_code == 400
