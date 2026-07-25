# backend/tests/test_tickets.py


def test_create_digital_ticket_success(api, client_headers, service_id):
    """Vérifie qu'un client connecté peut créer un ticket numérique."""
    response = api.post("/api/v1/tickets/digital", headers=client_headers, json={"service_id": service_id})
    assert response.status_code in [200, 201]
    data = response.json()
    assert "number" in data or "ticket_number" in data


def test_prevent_duplicate_ticket(api, client_headers, service_id):
    """Vérifie la règle métier : Refus d'un second ticket actif pour le même client[cite: 1]."""
    # Ticket 1 -> Réussit
    api.post("/api/v1/tickets/digital", headers=client_headers, json={"service_id": service_id})

    # Ticket 2 -> Refusé
    response2 = api.post("/api/v1/tickets/digital", headers=client_headers, json={"service_id": service_id})
    assert response2.status_code == 400
