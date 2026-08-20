"""
Health Check API Route
Provides system status, database connectivity verification, and metadata.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
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
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Checks database health via safe read-only query and returns structured status.
    """
    is_healthy = database.check_db_health()
    server_info = database.get_db_server_info() if is_healthy else {}
    tables = database.get_tables_list() if is_healthy else []

    db_status = DatabaseHealthStatus(
        status="connected" if is_healthy else "disconnected",
        healthy=is_healthy,
        database_name=server_info.get("database") if is_healthy else None,
        server_version=server_info.get("version") if is_healthy else None,
        total_tables=len(tables)
    )

    return HealthResponse(
        status="ok" if is_healthy else "degraded",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
        database=db_status
    )
