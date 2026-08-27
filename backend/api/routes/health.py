"""
Health Check API Route
Provides system status, database connectivity verification, and metadata.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status
from backend.config import Settings, get_settings
from backend.schemas.health import HealthResponse, DatabaseHealthStatus
import database

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System and Database Health Check",
    description="Returns API service health, timestamp, and read-only PostgreSQL connection status."
)
def get_health(
    response: Response,
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """
    Checks database health via safe read-only query and returns structured status.
    Returns HTTP 200 when database is healthy, HTTP 503 when disconnected or failing.
    Omit PostgreSQL server version and database name to prevent infrastructure fingerprinting.
    """
    is_healthy = database.check_db_health()
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    tables = database.get_tables_list() if is_healthy else []

    db_status = DatabaseHealthStatus(
        status="connected" if is_healthy else "disconnected",
        healthy=is_healthy,
        total_tables=len(tables)
    )

    return HealthResponse(
        status="ok" if is_healthy else "unhealthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
        database=db_status
    )
