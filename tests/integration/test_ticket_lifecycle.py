import pytest

pytestmark = pytest.mark.integration


def test_complete_digital_ticket_lifecycle(
    api, client_headers, cashier_headers, admin_headers, service_id
):
    created = api.post(
        "/api/v1/client/tickets", json={"service_id": service_id}, headers=client_headers
    )
    assert created.status_code == 201, created.text
    ticket = created.json()
    assert ticket["status"] == "WAITING"
    assert ticket["position"] == 1

    duplicate = api.post(
        "/api/v1/client/tickets", json={"service_id": service_id}, headers=client_headers
    )
    assert duplicate.status_code == 409

    counter = api.get("/api/v1/cashier/counters", headers=cashier_headers).json()[0]
    opened = api.patch(
        f"/api/v1/cashier/counters/{counter['id']}/status",
        json={"status": "OPEN"},
        headers=cashier_headers,
    )
    assert opened.status_code == 200

    called = api.post(
        f"/api/v1/cashier/counters/{counter['id']}/next-ticket", headers=cashier_headers
    )
    assert called.status_code == 200, called.text
    assert called.json()["id"] == ticket["id"]
    assert called.json()["status"] == "CALLED"

    started = api.patch(f"/api/v1/cashier/tickets/{ticket['id']}/start", headers=cashier_headers)
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"

    closed = api.patch(
        f"/api/v1/cashier/tickets/{ticket['id']}/close",
        json={"comment": "Service terminé", "auto_call_next": False},
        headers=cashier_headers,
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["current_ticket"] is None

    stats = api.get("/api/v1/admin/statistics/overview", headers=admin_headers)
    assert stats.status_code == 200
    assert stats.json()["completed"] == 1


def test_client_can_cancel_only_while_waiting(api, client_headers, service_id):
    ticket = api.post(
        "/api/v1/client/tickets", json={"service_id": service_id}, headers=client_headers
    ).json()
    cancelled = api.patch(f"/api/v1/client/tickets/{ticket['id']}/cancel", headers=client_headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_physical_ticket_joins_same_queue(api, agent_headers, cashier_headers, service_id):
    physical = api.post(
        "/api/v1/agent/tickets/physical",
        json={"service_id": service_id, "visitor_name": "Client sans téléphone"},
        headers=agent_headers,
    )
    assert physical.status_code == 201
    assert physical.json()["source"] == "PHYSICAL"
    assert physical.json()["position"] == 1
