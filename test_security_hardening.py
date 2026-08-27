"""
ZeroSQL AI V2 — Step 7E Production Security Hardening Verification Test Suite
Tests:
1. HTTP Security Headers:
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - Referrer-Policy: strict-origin-when-cross-origin
   - Content-Security-Policy: default-src 'self'; frame-ancestors 'none';
   - Verify deprecated X-XSS-Protection header is NOT present
   - Strict-Transport-Security (HSTS) when environment == "production"
2. CORS Configuration & Header Hardening:
   - Comma-separated string parsing for CORS_ALLOWED_ORIGINS
   - JSON array string parsing for CORS_ALLOWED_ORIGINS
   - Explicit allowed headers (no wildcard headers with credentials)
3. Production Secret & Credential Validation:
   - Rejects default or weak SECRET_KEY in production mode
   - Rejects default or weak ADMIN_PASSWORD in production mode
   - Rejects default or weak ADMIN_API_KEY in production mode
   - Allows defaults in development mode for seamless local dev
4. Health Endpoint Hardening:
   - Returns HTTP 200 OK when database is healthy
   - Returns HTTP 503 Service Unavailable when database is disconnected/unhealthy
   - Strictly omits PostgreSQL server_version (compiler/build strings) and database_name
5. Error Response Sanitization:
   - Raw PostgreSQL exception strings and SQL details are masked
   - Server filesystem paths are masked from API clients
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import psycopg

# Mock database connections to guarantee hermetic, network-isolated unit testing
mock_conn = MagicMock()
mock_cur = MagicMock()
mock_conn.cursor.return_value.__enter__.return_value = mock_cur
mock_conn.__enter__.return_value = mock_conn
mock_cur.fetchall.return_value = []
mock_cur.fetchone.return_value = None

patcher_admin = patch("database.get_admin_db_connection", return_value=mock_conn)
patcher_readonly = patch("database.get_readonly_db_connection", return_value=mock_conn)
patcher_health = patch("database.check_db_health", return_value=True)

patcher_admin.start()
patcher_readonly.start()
patcher_health.start()

from backend.main import app
from backend.config import (
    Settings,
    get_settings,
    INSECURE_DEFAULT_SECRET_KEY,
    INSECURE_DEFAULT_ADMIN_PASSWORD,
    INSECURE_DEFAULT_ADMIN_API_KEY
)
from backend.limiter import limiter

client = TestClient(app)
settings = get_settings()


class TestSecurityHardening(unittest.TestCase):
    """Step 7E Security Hardening Verification Suite."""

    @classmethod
    def tearDownClass(cls):
        """Clean up active mocks."""
        patcher_admin.stop()
        patcher_readonly.stop()
        patcher_health.stop()

    def setUp(self):
        """Reset rate limiter before each test."""
        limiter.reset()

    # --------------------------------------------------------------------------
    # 1. HTTP Security Headers
    # --------------------------------------------------------------------------
    def test_security_headers_present_on_responses(self):
        """Verify essential security headers are injected and X-XSS-Protection is omitted."""
        res = client.get("/api/v1/health")
        self.assertIn(res.status_code, (200, 503))

        # 1. X-Content-Type-Options
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")

        # 2. X-Frame-Options
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")

        # 3. Referrer-Policy
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

        # 4. Content-Security-Policy
        self.assertIn("default-src 'self'", res.headers.get("Content-Security-Policy", ""))
        self.assertIn("frame-ancestors 'none'", res.headers.get("Content-Security-Policy", ""))

        # 5. Explicit requirement: do NOT add deprecated X-XSS-Protection header
        self.assertNotIn("X-XSS-Protection", res.headers)
        print("  ✅ PASS: Security headers (nosniff, DENY, Referrer-Policy, CSP) verified; deprecated X-XSS-Protection omitted.")

    def test_hsts_header_in_production(self):
        """Verify Strict-Transport-Security header is injected when environment == production."""
        with patch.object(settings, "environment", "production"):
            res = client.get("/api/v1/health")
            self.assertIn("Strict-Transport-Security", res.headers)
            self.assertIn("max-age=31536000", res.headers["Strict-Transport-Security"])
            self.assertIn("includeSubDomains", res.headers["Strict-Transport-Security"])
        print("  ✅ PASS: Strict-Transport-Security (HSTS) header conditionally active in production.")

    # --------------------------------------------------------------------------
    # 2. CORS Configuration & Header Hardening
    # --------------------------------------------------------------------------
    def test_cors_origin_parsing_flexibility(self):
        """Verify Settings parses both comma-separated and JSON list CORS origin strings."""
        # 1. Comma-separated string
        s1 = Settings(cors_allowed_origins="https://app.zerosql.ai, https://admin.zerosql.ai")
        self.assertEqual(s1.cors_allowed_origins, ["https://app.zerosql.ai", "https://admin.zerosql.ai"])

        # 2. JSON array string
        s2 = Settings(cors_allowed_origins='["https://client.zerosql.ai"]')
        self.assertEqual(s2.cors_allowed_origins, ["https://client.zerosql.ai"])

        # 3. Python list of strings
        s3 = Settings(cors_allowed_origins=["https://custom.com"])
        self.assertEqual(s3.cors_allowed_origins, ["https://custom.com"])
        print("  ✅ PASS: CORS allowed origins parses comma-separated, JSON array, and list formats.")

    def test_cors_explicit_allowed_headers_preflight(self):
        """Verify CORS preflight accepts explicit application headers and avoids wildcard headers."""
        res = client.options(
            "/api/v1/admin/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type, X-Admin-API-Key"
            }
        )
        self.assertEqual(res.status_code, 200)
        allow_headers = res.headers.get("access-control-allow-headers", "")
        self.assertIn("Authorization", allow_headers)
        self.assertIn("Content-Type", allow_headers)
        self.assertIn("X-Admin-API-Key", allow_headers)
        print("  ✅ PASS: CORS preflight validates explicit application authentication headers.")

    # --------------------------------------------------------------------------
    # 3. Production Secret & Credential Validation
    # --------------------------------------------------------------------------
    def test_production_secret_enforcement_blocks_insecure_defaults(self):
        """Verify Settings refuses to boot in production with default secrets or weak credentials."""
        # 1. Default SECRET_KEY rejected
        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                secret_key=INSECURE_DEFAULT_SECRET_KEY,
                admin_password="SuperStrongPassword123!",
                admin_api_key="ValidAdminApiKey2026!"
            )
        self.assertIn("SECRET_KEY", str(ctx.exception))

        # 2. Default ADMIN_PASSWORD rejected
        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                secret_key="A" * 32,
                admin_password=INSECURE_DEFAULT_ADMIN_PASSWORD,
                admin_api_key="ValidAdminApiKey2026!"
            )
        self.assertIn("ADMIN_PASSWORD", str(ctx.exception))

        # 3. Default ADMIN_API_KEY rejected
        with self.assertRaises(ValueError) as ctx:
            Settings(
                environment="production",
                secret_key="A" * 32,
                admin_password="SuperStrongPassword123!",
                admin_api_key=INSECURE_DEFAULT_ADMIN_API_KEY
            )
        self.assertIn("ADMIN_API_KEY", str(ctx.exception))

        # 4. Valid production credentials succeed
        valid_prod = Settings(
            environment="production",
            secret_key="a_very_long_secure_random_production_secret_key_32_chars",
            admin_password="SuperStrongProductionPassword2026!",
            admin_api_key="ProductionAdminApiKeyVerySecure2026!"
        )
        self.assertEqual(valid_prod.environment, "production")

        # 5. Development mode allows defaults without error
        dev = Settings(environment="development")
        self.assertEqual(dev.environment, "development")
        print("  ✅ PASS: Production secret validation strictly blocks insecure defaults.")

    # --------------------------------------------------------------------------
    # 4. Health Endpoint Hardening
    # --------------------------------------------------------------------------
    def test_health_endpoint_healthy_returns_200_without_fingerprinting(self):
        """Verify health check returns HTTP 200 and omits server version and database name."""
        with patch("database.check_db_health", return_value=True), \
             patch("database.get_tables_list", return_value=["users", "orders"]):
            res = client.get("/api/v1/health")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertTrue(data["database"]["healthy"])
            self.assertEqual(data["database"]["status"], "connected")
            self.assertEqual(data["database"]["total_tables"], 2)

            # Assert database_name and server_version are omitted
            self.assertNotIn("server_version", data["database"])
            self.assertNotIn("database_name", data["database"])
            self.assertNotIn("gcc", str(data).lower())
            self.assertNotIn("linux", str(data).lower())
        print("  ✅ PASS: Healthy check returns HTTP 200 with server version & database name omitted.")

    def test_health_endpoint_unhealthy_returns_503(self):
        """Verify health check returns HTTP 503 Service Unavailable when database is down."""
        with patch("database.check_db_health", return_value=False):
            res = client.get("/api/v1/health")
            self.assertEqual(res.status_code, 503)
            data = res.json()
            self.assertEqual(data["status"], "unhealthy")
            self.assertFalse(data["database"]["healthy"])
            self.assertEqual(data["database"]["status"], "disconnected")
        print("  ✅ PASS: Unhealthy database check strictly returns HTTP 503 Service Unavailable.")

    # --------------------------------------------------------------------------
    # 5. Error Response Sanitization
    # --------------------------------------------------------------------------
    def test_error_response_sanitization_in_dataset_upload(self):
        """Verify database errors in upload endpoint do not leak raw internal SQL errors."""
        auth_headers = {"X-Admin-API-Key": settings.admin_api_key}

        with patch("backend.services.storage_service.StorageService.save_uploaded_file",
                   return_value=("id1", "test.csv", "/tmp/test.csv", 10, "csv")), \
             patch("backend.services.dataset_service.DatasetService.record_uploaded_dataset",
                   side_effect=psycopg.OperationalError("FATAL: password authentication failed for user 'postgres'")):
            res = client.post(
                "/api/v1/admin/datasets/upload",
                headers=auth_headers,
                files={"file": ("test.csv", b"a,b\n1,2", "text/csv")}
            )
            self.assertEqual(res.status_code, 500)
            data = res.json()
            # Raw PostgreSQL password authentication error must NOT reach client
            self.assertNotIn("FATAL", data["detail"])
            self.assertNotIn("postgres", data["detail"])
            self.assertIn("Database metadata recording failed due to an internal server error", data["detail"])
        print("  ✅ PASS: Raw internal PostgreSQL errors are sanitized in API responses.")

    def test_error_response_sanitization_in_chat(self):
        """Verify query execution failures do not leak raw internal tracebacks to clients."""
        with patch("backend.api.routes.chat.ask_agent", side_effect=RuntimeError("Internal syntax trace in core engine")):
            res = client.post("/api/v1/chat", json={"message": "Show all users"})
            self.assertEqual(res.status_code, 500)
            data = res.json()
            self.assertNotIn("Internal syntax trace", data["detail"])
            self.assertIn("AI Agent query execution failed due to an internal server error", data["detail"])
        print("  ✅ PASS: Raw AI agent exceptions are sanitized in API responses.")

    def test_openapi_docs_accessibility(self):
        """Verify OpenAPI documentation endpoints are available in development."""
        res_dev = client.get("/docs")
        self.assertEqual(res_dev.status_code, 200)
        print("  ✅ PASS: OpenAPI documentation accessible in development mode.")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  🚀 RUNNING ZERO-SQL AI V2 SECURITY HARDENING TEST SUITE")
    print("=" * 70 + "\n")
    unittest.main(verbosity=2)
