"""
Authentication Pydantic Schemas
Models for admin login and token verification.
"""

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    """Admin credentials login request payload."""
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class AdminLoginResponse(BaseModel):
    """Admin login response containing authentication token."""
    access_token: str = Field(description="Bearer authentication token")
    token_type: str = Field(default="bearer", description="Token type")
    username: str = Field(description="Authenticated username")
    expires_in_minutes: int = Field(description="Token validity duration in minutes")
