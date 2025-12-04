import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    candidate_hash = hash_api_key(api_key)
    return secrets.compare_digest(candidate_hash, stored_hash)


def sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def validate_signature(secret: str, payload: bytes, signature: str) -> None:
    expected = sign_payload(secret, payload)
    if not secrets.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid signature",
        )


def verify_idempotency(existing_fingerprint: str | None, new_fingerprint: str) -> None:
    if existing_fingerprint and existing_fingerprint == new_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="duplicate request"
        )


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
