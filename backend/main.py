"""
ZeroSQL AI - FastAPI Application Entry Point (V2)
Main ASGI application initialization, middleware configuration, and router setup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.logging_config import setup_logging
from backend.api.routes.health import router as health_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.datasets import router as dataset_router, public_router as public_dataset_router
from backend.api.routes.chat import router as chat_router
from backend.services.dataset_service import init_dataset_metadata_table

settings = get_settings()
logger = setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} in [{settings.environment}] mode...")
    init_dataset_metadata_table()
    logger.info("Database metadata tables verified.")
    yield
    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI Backend for ZeroSQL AI: Secure Dataset Management & Natural Language Analytics",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware setup with configurable, secure origins (Step 6 Hardening)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global unhandled exception handler.
    Logs error securely to server output and returns clean, non-leaking HTTP 500.
    """
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request."}
    )


# Root-level health endpoint
app.include_router(health_router, prefix="")

# Versioned API Routes (/api/v1)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dataset_router, prefix="/api/v1")
app.include_router(public_dataset_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root_endpoint():
    """Root status endpoint providing API information and documentation links."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1": {
            "health": "/api/v1/health",
            "admin_login": "/api/v1/admin/auth/login",
            "dataset_upload": "/api/v1/admin/datasets/upload",
            "dataset_list": "/api/v1/admin/datasets",
            "dataset_catalog": "/api/v1/datasets/catalog",
            "recommendations": "/api/v1/datasets/recommendations",
            "chat": "/api/v1/chat"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
