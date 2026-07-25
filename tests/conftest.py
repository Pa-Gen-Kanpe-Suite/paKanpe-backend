import os

# Ajustement de la base de données de test et des secrets
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["JWT_SECRET"] = "test-secret-with-more-than-thirty-two-characters"
os.environ["NO_SHOW_GRACE_SECONDS"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models import Bank, Counter, CounterStatus, Service, User, UserRole


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        bank = Bank(name="PA GEN KANPE BANK", branch_name="Agence Principale")
        db.add(bank)
        db.flush()
        db.add_all(
            [
                Service(
                    bank_id=bank.id,
                    code="DEPOT",
                    name="Dépôt",
                    average_minutes=5,
                ),
                Service(
                    bank_id=bank.id,
                    code="RETRAIT",
                    name="Retrait",
                    average_minutes=5,
                ),
                Counter(
                    bank_id=bank.id,
                    number=1,
                    name="Guichet 1",
                    status=CounterStatus.CLOSED.value,
                ),
                User(
                    bank_id=bank.id,
                    full_name="Agent Test",
                    email="agent@test.ht",
                    phone="+50930000001",
                    password_hash=hash_password("Agent123!"),
                    role=UserRole.AGENT.value,
                ),
                User(
                    bank_id=bank.id,
                    full_name="Caissier Test",
                    email="cashier@test.ht",
                    phone="+50930000002",
                    password_hash=hash_password("Cashier123!"),
                    role=UserRole.CASHIER.value,
                ),
                User(
                    bank_id=bank.id,
                    full_name="Admin Test",
                    email="admin@test.ht",
                    phone="+50930000003",
                    password_hash=hash_password("Admin123!"),
                    role=UserRole.ADMIN.value,
                ),
            ]
        )
        db.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Surcharge NO_SHOW_GRACE_SECONDS à 0 et vide le cache Pydantic/lru_cache pour les tests."""
    settings = get_settings()
    monkeypatch.setattr(settings, "NO_SHOW_GRACE_SECONDS", 0)
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


@pytest.fixture
def api():
    with TestClient(app) as test_client:
        yield test_client


def login(api: TestClient, email: str, password: str) -> dict[str, str]:
    response = api.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def cashier_headers(api):
    return login(api, "cashier@test.ht", "Cashier123!")


@pytest.fixture
def agent_headers(api):
    return login(api, "agent@test.ht", "Agent123!")


@pytest.fixture
def admin_headers(api):
    return login(api, "admin@test.ht", "Admin123!")


@pytest.fixture
def client_headers(api):
    response = api.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Client Test",
            "email": "client@test.ht",
            "phone": "+50940000001",
            "bank_identifier": "C-001",
            "password": "Client123!",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def service_id():
    with SessionLocal() as db:
        return db.scalar(select(Service.id).where(Service.code == "DEPOT"))