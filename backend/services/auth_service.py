"""
Admin Authentication Service
Provides secure token generation, verification, and password validation.
"""

import hmac
import hashlib
import base64
import json
import time
import secrets
from typing import Optional
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from backend.config import Settings, get_settings

security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    """Returns SHA-256 hash of plaintext password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, expected_password: str) -> bool:
    """Timing-attack-safe comparison of password."""
    return secrets.compare_digest(plain_password, expected_password)


def create_access_token(username: str, settings: Settings) -> str:
    """
    Generates a cryptographically signed HMAC-SHA256 bearer token.
    Payload contains username, issued_at timestamp, and expiry timestamp.
    """
    now = int(time.time())
    expires_at = now + (settings.token_expire_minutes * 60)
    
    payload = {
        "sub": username,
        "iat": now,
        "exp": expires_at,
        "role": "admin"
    }
    
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        settings.secret_key.encode('utf-8'),
        encoded_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded_payload}.{signature}"


def verify_access_token(token: str, settings: Settings) -> Optional[dict]:
    """
    Verifies token HMAC signature and expiration.
    Returns decoded payload if valid, None otherwise.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
            
        encoded_payload, signature = parts
        
        # Verify HMAC signature
        expected_sig = hmac.new(
            settings.secret_key.encode('utf-8'),
            encoded_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not secrets.compare_digest(signature, expected_sig):
            return None
            
        # Decode payload
        padding = '=' * (-len(encoded_payload) % 4)
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + padding)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None
            
        return payload
    except Exception:
        return None


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(api_key_header),
    settings: Settings = Depends(get_settings)
) -> str:
    """
    FastAPI dependency for verifying admin authorization.
    Accepts either Bearer token in Authorization header or X-Admin-API-Key header.
    Raises HTTP 401 Unauthorized if verification fails.
    """
    # 1. Check API Key header if provided
    if api_key and settings.admin_api_key and secrets.compare_digest(api_key, settings.admin_api_key):
        return settings.admin_username

    # 2. Check Bearer Token
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        payload = verify_access_token(token, settings)
        if payload and payload.get("sub") == settings.admin_username:
            return payload["sub"]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid Admin credentials or Bearer token required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
