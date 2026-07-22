import pytest

pytestmark = pytest.mark.integration


def test_register_login_and_me(api, client_headers):
    me = api.get("/api/v1/auth/me", headers=client_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "CLIENT"

    login = api.post(
        "/api/v1/auth/login",
        json={"email": "client@test.ht", "password": "Client123!"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_role_is_enforced(api, client_headers):
    response = api.get("/api/v1/admin/counters", headers=client_headers)
    assert response.status_code == 403


def test_invalid_credentials_are_rejected(api):
    response = api.post("/api/v1/auth/login", json={"email": "admin@test.ht", "password": "wrong"})
    assert response.status_code == 401
