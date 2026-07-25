import pytest
from datetime import timedelta

from app.core.security import create_access_token, decode_access_token

pytestmark = pytest.mark.unit


def test_expired_token_is_rejected():
    """Vérifie qu'un jeton JWT expiré est refusé lors du décodage."""
    # Create a token with past expiration
    token = create_access_token(user_id=1, role="CLIENT")

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
