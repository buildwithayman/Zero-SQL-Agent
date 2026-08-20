"""
ZeroSQL AI V2 - Backend Configuration Layer
Centralized, validated settings using Pydantic Settings and environment variables.
"""

import os
from functools import lru_cache
from typing import Optional
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

    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", description="FastAPI server host bind address")
    api_port: int = Field(default=8000, description="FastAPI server port")

    # Database URLs (Separated Dual-Role Architecture)
    database_url: Optional[str] = Field(default=None, description="Primary database connection string")
    database_readonly_url: Optional[str] = Field(default=None, description="Dedicated read-only connection string for AI Agent")
    database_admin_url: Optional[str] = Field(default=None, description="Dedicated admin write connection string for backend ingestion")

    # AI Engine Configuration
    groq_api_key: Optional[str] = Field(default=None, description="Groq Cloud API Key")
    groq_model: str = Field(default="openai/gpt-oss-120b", description="Default LLM model identifier")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

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
