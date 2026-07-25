# backend/tests/integration/test_validation.py
import pytest

pytestmark = pytest.mark.integration


def test_register_invalid_email_and_phone(api):
    """Vérifie que la création de compte échoue si l'email ou le téléphone est invalide."""
    response = api.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "not-an-email",  # Email invalide
            "phone": "123",  # Téléphone trop court
            "password": "Short",  # Mot de passe faible
        },
    )
    assert response.status_code == 422
