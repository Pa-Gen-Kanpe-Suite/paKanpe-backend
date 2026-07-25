# backend/tests/unit/test_jwt_expiration.py
from datetime import timedelta

import pytest

from app.core.security import create_access_token, decode_access_token

pytestmark = pytest.mark.unit


def test_expired_token_is_rejected():
    """Vérifie qu'un jeton JWT expiré est refusé lors du décodage."""
    # Création d'un token expiré il y a 10 minutes
    expired_token = create_access_token(user_id=1, role="CLIENT", expires_delta=timedelta(minutes=-10))

    payload = decode_access_token(expired_token)
    assert payload is None
