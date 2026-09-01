from backend.auth.auth import create_access_token, decode_token, hash_password, verify_password


def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_create_and_decode():
    token = create_access_token({"sub": "user-123", "role": "user", "type": "access"})
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "user"
    assert decoded["type"] == "access"
