import uuid
from datetime import timedelta

import jwt
import pytest

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.app.core.timeutil import utcnow

pytestmark = pytest.mark.req("NFR-04", "NFR-05")


def test_password_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert hashed.startswith("$2")  # bcrypt
    assert verify_password("Secret123", hashed)
    assert not verify_password("secret123", hashed)


def test_same_password_produces_different_hashes():
    assert hash_password("Secret123") != hash_password("Secret123")


def test_verify_password_handles_garbage_hash():
    assert verify_password("x", "not-a-hash") is False


def test_token_round_trip_contains_subject_and_role():
    uid = uuid.uuid4()
    payload = decode_access_token(create_access_token(uid, "STAFF"))
    assert payload["sub"] == str(uid)
    assert payload["role"] == "STAFF"
    assert payload["exp"] - payload["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_expired_token_is_rejected():
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": int((utcnow() - timedelta(minutes=1)).timestamp())},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_signed_with_other_key_is_rejected():
    token = jwt.encode({"sub": str(uuid.uuid4())}, "another-key-of-sufficient-length-1234567890", algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)


def test_production_defaults_are_secure():
    from backend.app.core.config import Settings

    fields = Settings.model_fields
    assert fields["BCRYPT_ROUNDS"].default >= 12
    assert fields["ACCESS_TOKEN_EXPIRE_MINUTES"].default == 30
