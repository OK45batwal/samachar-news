"""Test auth utilities — password hashing + JWT."""
from backend.auth.auth import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    pw = "SecurePass123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_jwt_create_and_decode():
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload
