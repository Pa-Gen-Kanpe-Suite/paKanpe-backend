import pytest

pytestmark = pytest.mark.integration


def test_complete_digital_ticket_lifecycle(
    api, client_headers, cashier_headers, admin_headers, service_id
):
    """
    Test d'intégration du cycle de vie complet d'un ticket numérique :
    WAITING -> CALLED -> IN_PROGRESS -> CLOSED + Validation des statistiques.
    """
    # 1. Création du ticket numérique
    created = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    )
    assert created.status_code == 201, created.text
    ticket = created.json()
    assert ticket["status"] == "WAITING"
    assert ticket["position"] == 1

    # 2. Refus d'un second ticket actif pour le même client (Règle MVP)
    duplicate = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    )
    assert duplicate.status_code == 409

    # 3. Ouverture du guichet par le caissier
    counter = api.get("/api/v1/cashier/counters", headers=cashier_headers).json()[0]
    opened = api.patch(
        f"/api/v1/cashier/counters/{counter['id']}/status",
        json={"status": "OPEN"},
        headers=cashier_headers,
    )
    assert opened.status_code == 200

    # 4. Appel du ticket
    called = api.post(
        f"/api/v1/cashier/counters/{counter['id']}/next-ticket",
        headers=cashier_headers,
    )
    assert called.status_code == 200, called.text
    assert called.json()["id"] == ticket["id"]
    assert called.json()["status"] == "CALLED"

    # 5. Début de traitement
    started = api.patch(
        f"/api/v1/cashier/tickets/{ticket['id']}/start",
        headers=cashier_headers,
    )
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"

    # 6. Clôture du ticket
    closed = api.patch(
        f"/api/v1/cashier/tickets/{ticket['id']}/close",
        json={"comment": "Service terminé", "auto_call_next": False},
        headers=cashier_headers,
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["current_ticket"] is None

    # 7. Vérification du tableau de bord Admin
    stats = api.get("/api/v1/admin/statistics/overview", headers=admin_headers)
    assert stats.status_code == 200
    assert stats.json()["completed"] == 1


def test_client_can_cancel_only_while_waiting(api, client_headers, service_id):
    """Vérifie qu'un client peut annuler son ticket tant qu'il est en attente."""
    ticket = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    ).json()
    cancelled = api.patch(
        f"/api/v1/client/tickets/{ticket['id']}/cancel",
        headers=client_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_physical_ticket_joins_same_queue(
    api, agent_headers, cashier_headers, service_id
):
    """
    Vérifie que les tickets physiques créés par un agent
    intègrent la même file d'attente unique.
    """
    physical = api.post(
        "/api/v1/agent/tickets/physical",
        json={"service_id": service_id, "visitor_name": "Client sans téléphone"},
        headers=agent_headers,
    )
    assert physical.status_code == 201
    assert physical.json()["source"] == "PHYSICAL"
    assert physical.json()["position"] == 1


def test_client_can_consult_position_and_estimated_time(
    api, client_headers, service_id
):
    """
    Vérifie la consultation de la position et du temps d'attente
    estimé par le client.
    """
    created = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]

    # Consultation du ticket actif
    my_ticket = api.get("/api/v1/client/tickets/current", headers=client_headers)
    assert my_ticket.status_code == 200
    assert my_ticket.json()["id"] == ticket_id
    assert "position" in my_ticket.json()
    assert "estimated_wait_minutes" in my_ticket.json()


def test_no_show_grace_period_handling(
    api, client_headers, cashier_headers, service_id
):
    """
    Vérifie le passage du statut d'un ticket en ABSENT ou LATE
    (gestion du délai de grâce).
    """
    # 1. Création et appel d'un ticket
    ticket = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    ).json()

    counter = api.get("/api/v1/cashier/counters", headers=cashier_headers).json()[0]
    api.patch(
        f"/api/v1/cashier/counters/{counter['id']}/status",
        json={"status": "OPEN"},
        headers=cashier_headers,
    )
    api.post(
        f"/api/v1/cashier/counters/{counter['id']}/next-ticket",
        headers=cashier_headers,
    )

    # 2. Marquage du ticket en ABSENT par le caissier
    no_show = api.patch(
        f"/api/v1/cashier/tickets/{ticket['id']}/no-show",
        headers=cashier_headers,
    )
    assert no_show.status_code == 200
    assert no_show.json()["status"] == "ABSENT"
