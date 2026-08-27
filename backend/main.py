"""
ZeroSQL AI - FastAPI Application Entry Point (V2)
Main ASGI application initialization, middleware configuration, and router setup.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.config import get_settings
from backend.logging_config import setup_logging
from backend.limiter import limiter
from backend.api.routes.health import router as health_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.datasets import router as dataset_router, public_router as public_dataset_router
from backend.api.routes.chat import router as chat_router
import database
from backend.services.dataset_service import init_dataset_metadata_table

settings = get_settings()
logger = setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} in [{settings.environment}] mode...")
    database.init_db_pools(
        min_size_ro=settings.db_pool_readonly_min,
        max_size_ro=settings.db_pool_readonly_max,
        min_size_admin=settings.db_pool_admin_min,
        max_size_admin=settings.db_pool_admin_max,
        timeout=settings.db_pool_timeout,
        connect_timeout=settings.db_connect_timeout,
        sslmode=settings.db_sslmode
    )
    logger.info("Database connection pools initialized.")
    init_dataset_metadata_table()
    logger.info("Database metadata tables verified.")
    yield
    logger.info("Closing database connection pools...")
    database.close_db_pools()
    logger.info("Database connection pools closed.")
    logger.info(f"Shutting down {settings.app_name}...")


is_production = settings.environment.lower() == "production"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI Backend for ZeroSQL AI: Secure Dataset Management & Natural Language Analytics",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    lifespan=lifespan
)

# Attach SlowAPI limiter instance to FastAPI application state
app.state.limiter = limiter

# Rate Limiting Middleware
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware setup with configurable, secure origins (Step 6 Hardening)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Admin-API-Key",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Injects production HTTP security headers onto every outgoing response.
    Protects against MIME-confusion, clickjacking, referrer leakage, and protocol downgrade.
    Explicitly omits deprecated X-XSS-Protection header per Step 7E specification.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    if settings.environment.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom exception handler for RateLimitExceeded.
    Returns clean, non-leaking HTTP 429 JSON response with Retry-After header.
    """
    retry_after = 60
    try:
        if hasattr(request.state, "view_rate_limit") and request.state.view_rate_limit:
            current_limit = request.state.view_rate_limit
            window_stats = limiter.limiter.get_window_stats(current_limit[0], *current_limit[1])
            reset_in = 1 + window_stats[0]
            retry_after = max(1, int(reset_in - time.time()))
    except Exception:
        pass

    logger.warning(f"Rate limit exceeded on {request.method} {request.url.path}")
    content = {
        "error": "RateLimitExceeded",
        "detail": "Too many requests. Please try again later.",
        "retry_after": retry_after
    }
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=content,
        headers={"Retry-After": str(retry_after)}
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
