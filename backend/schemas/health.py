"""
Health Check Pydantic Schemas
Structured models for system and database health reporting.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseHealthStatus(BaseModel):
    """Database connectivity and table status model."""
    status: str = Field(description="Database connectivity status: 'connected' or 'disconnected'")
    healthy: bool = Field(description="True if database responds to health ping")
    total_tables: int = Field(default=0, description="Number of public tables detected")


class HealthResponse(BaseModel):
    """System health check response schema."""
    status: str = Field(default="ok", description="Overall API service health status")
    app_name: str = Field(description="Application title")
    version: str = Field(description="Application version")
    environment: str = Field(description="Runtime environment")
    timestamp: datetime = Field(description="Current server UTC timestamp")
    database: DatabaseHealthStatus = Field(description="PostgreSQL health breakdown")
