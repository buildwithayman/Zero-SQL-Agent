"""
ZeroSQL AI V2 - Backend Configuration Layer
Centralized, validated settings using Pydantic Settings and environment variables.
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables and .env file.
    Sensitive credentials are never exposed in public models or string representations.
    """
    # Application Information
    app_name: str = Field(default="ZeroSQL AI V2 API", description="Application Title")
    app_version: str = Field(default="2.0.0-alpha", description="API Version")
    environment: str = Field(default="development", description="Runtime environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode flag")
    log_level: str = Field(default="INFO", description="Server logging level (DEBUG, INFO, WARNING, ERROR)")

    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", description="FastAPI server host bind address")
    api_port: int = Field(default=8000, description="FastAPI server port")

    # CORS Configuration (Step 6 Hardening - Configurable Origins)
    cors_allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8501",
            "http://127.0.0.1:8501"
        ],
        description="Allowed CORS origin URLs for React frontend and Streamlit"
    )

    # Database URLs (Separated Dual-Role Architecture)
    database_url: Optional[str] = Field(default=None, description="Primary database connection string")
    database_readonly_url: Optional[str] = Field(default=None, description="Dedicated read-only connection string for AI Agent")
    database_admin_url: Optional[str] = Field(default=None, description="Dedicated admin write connection string for backend ingestion")

    # AI Engine Configuration
    groq_api_key: Optional[str] = Field(default=None, description="Groq Cloud API Key")
    groq_model: str = Field(default="openai/gpt-oss-120b", description="Default LLM model identifier")

    # Admin Authentication Configuration (Step 2)
    admin_username: str = Field(default="admin", description="Admin username for management portal")
    admin_password: str = Field(default="admin123", description="Admin password for authentication")
    admin_api_key: Optional[str] = Field(default="zerosql-admin-secret-key-2026", description="Static Admin API Key alternative")
    secret_key: str = Field(default="zerosql-super-secret-hmac-jwt-key-2026", description="Secret key for signing auth tokens")
    token_expire_minutes: int = Field(default=1440, description="Auth token expiration in minutes (24 hours)")

    # Dataset Storage & Upload Limits (Step 2)
    upload_dir: str = Field(default="data/uploads", description="Directory to store uploaded dataset files")
    max_upload_size_mb: int = Field(default=50, description="Maximum allowed dataset upload size in megabytes")
    allowed_extensions: List[str] = Field(
        default=["csv", "xlsx", "json", "parquet"],
        description="Strictly allowed dataset file extensions"
    )

    # External Network Fetch Timeout
    external_fetch_timeout_sec: float = Field(default=10.0, description="Timeout in seconds for external dataset downloads")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Returns max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def effective_readonly_db_url(self) -> Optional[str]:
        """Returns the read-only database URL, falling back to primary database_url."""
        return self.database_readonly_url or self.database_url

    @property
    def effective_admin_db_url(self) -> Optional[str]:
        """Returns the admin write database URL, falling back to primary database_url."""
        return self.database_admin_url or self.database_url


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of the Settings object.
    Ensures environment variables and .env are parsed only once.
    """
    return Settings()
