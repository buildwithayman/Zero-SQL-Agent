"""
Admin Authentication Routes
Handles admin login and token generation.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from backend.config import Settings, get_settings
from backend.schemas.auth import AdminLoginRequest, AdminLoginResponse
from backend.services.auth_service import verify_password, create_access_token

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Admin Authentication Login",
    description="Authenticates admin credentials and returns an access token."
)
def admin_login(
    payload: AdminLoginRequest,
    settings: Settings = Depends(get_settings)
) -> AdminLoginResponse:
    """
    Validates admin username and password.
    Returns timed cryptographic Bearer token.
    """
    # Safe constant-time comparison
    is_valid_user = verify_password(payload.username, settings.admin_username)
    is_valid_pass = verify_password(payload.password, settings.admin_password)

    if not (is_valid_user and is_valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(settings.admin_username, settings)

    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        username=settings.admin_username,
        expires_in_minutes=settings.token_expire_minutes
    )
