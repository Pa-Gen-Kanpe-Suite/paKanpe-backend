import pytest

pytestmark = pytest.mark.integration


def test_absence_is_terminal_and_ticket_leaves_queue(
    api, client_headers, cashier_headers, service_id
):
    """
    Vérifie qu'un ticket marqué ABSENT sort de la file d'attente active
    et que l'écran d'affichage principal (Display) met à jour le nombre d'attentistes.
    """
    # 1. Le client crée un ticket numérique
    ticket = api.post(
        "/api/v1/client/tickets",
        json={"service_id": service_id},
        headers=client_headers,
    ).json()

    # 2. Le caissier ouvre son guichet et appelle le ticket
    counter = api.get("/api/v1/cashier/counters", headers=cashier_headers).json()[0]
    api.patch(
        f"/api/v1/cashier/counters/{counter['id']}/status",
        json={"status": "OPEN"},
        headers=cashier_headers,
    )
    api.post(
        f"/api/v1/cashier/counters/{counter['id']}/next-ticket", headers=cashier_headers
    )

    # 3. Le caissier constate l'absence du client et valide le "no-show"
    absent = api.patch(
        f"/api/v1/cashier/tickets/{ticket['id']}/no-show", headers=cashier_headers
    )
    assert absent.status_code == 200, absent.text
    assert absent.json()["status"] == "ABSENT"
    assert absent.json()["position"] is None  # Le ticket n'a plus de rang actif

    # 4. Vérification de l'API Display (Écran d'affichage public)
    display = api.get("/api/v1/display")
    assert display.status_code == 200
    assert (
        display.json()["waiting_count"] == 0
    )  # La file d'attente est bien retombée à zéro
