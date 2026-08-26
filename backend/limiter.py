"""
ZeroSQL AI V2 — Centralized Rate Limiter
Configures SlowAPI Limiter using client IP address extraction.

Storage Architecture:
- Single-Instance Deployment: Uses default in-memory storage (thread-safe for single process).
- Horizontally Scaled Deployment (Multi-worker/cluster):
  Configure shared Redis storage (e.g. storage_uri="redis://redis-host:6379/0").
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Centralized Limiter instance
# headers_enabled is set to False so SlowAPI doesn't mandate 'response: Response' on all route signatures.
# The custom RateLimitExceeded exception handler in backend/main.py injects the standard Retry-After header.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=False
)
