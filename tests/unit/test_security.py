import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_password_is_hashed_and_verified():
    """Vérifie le hachage sécurisé et la validation des mots de passe."""
    hashed = hash_password("Secret123!")

    # 1. Le mot de passe ne doit jamais être conservé en texte brut
    assert hashed != "Secret123!"

    # 2. Vérification des cas valide et invalide
    assert verify_password("Secret123!", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_contains_identity_and_role():
    """Vérifie que le jeton JWT généré contient bien l'ID utilisateur (sub) et son rôle (RBAC)."""
    token = create_access_token(42, "CLIENT")
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "CLIENT"
