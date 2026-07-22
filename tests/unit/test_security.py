from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verified():
    hashed = hash_password("Secret123!")
    assert hashed != "Secret123!"
    assert verify_password("Secret123!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_contains_identity_and_role():
    token = create_access_token(42, "CLIENT")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "CLIENT"
