"""
ZeroSQL AI V2 — Production Rate Limiting Verification Test Suite
Tests rate limiting enforcement across all protected endpoints:
- Admin Login (5/min)
- AI Chat (10/min)
- Dataset Upload (5/min)
- Dataset Process (5/min)
- Dataset Import (5/min)
- Public Catalog (60/min)
- HTTP 429 JSON response structure & Retry-After header
- Invariant: Health check is not rate limited
- Invariant: SQL Security validator remains 100% passing
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

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
from backend.limiter import limiter
from backend.config import get_settings
from sql_validator import validate_sql

client = TestClient(app)
settings = get_settings()


class TestRateLimiting(unittest.TestCase):
    """Test suite for SlowAPI rate limiting integration."""

    @classmethod
    def tearDownClass(cls):
        """Clean up active mocks."""
        patcher_admin.stop()
        patcher_readonly.stop()
        patcher_health.stop()

    def setUp(self):
        """Reset rate limiter counters before each test method."""
        limiter.reset()

    def test_admin_login_rate_limiting(self):
        """
        Verify POST /api/v1/admin/auth/login allows up to 5 attempts per minute,
        and strictly returns HTTP 429 on the 6th attempt.
        """
        payload = {"username": "admin", "password": "wrong_password_test"}

        # First 5 attempts: rejected by auth with 401, NOT 429
        for i in range(1, 6):
            response = client.post("/api/v1/admin/auth/login", json=payload)
            self.assertEqual(
                response.status_code,
                401,
                f"Attempt {i} expected 401 Unauthorized, got {response.status_code}"
            )

        # 6th attempt: Rate limit exceeded -> HTTP 429
        blocked = client.post("/api/v1/admin/auth/login", json=payload)
        self.assertEqual(blocked.status_code, 429, f"Expected 429, got {blocked.status_code}")

        data = blocked.json()
        self.assertEqual(data.get("error"), "RateLimitExceeded")
        self.assertIn("Too many requests", data.get("detail", ""))
        self.assertIn("retry_after", data)
        self.assertIn("Retry-After", blocked.headers)
        self.assertGreater(int(blocked.headers["Retry-After"]), 0)
        print("  ✅ PASS: Admin login rate limit (5/min) and HTTP 429 with Retry-After verified.")

    def test_chat_rate_limiting(self):
        """
        Verify POST /api/v1/chat allows 10 requests per minute and blocks on 11th.
        """
        payload = {"message": "   "}  # Bad request (empty message)

        for i in range(1, 11):
            response = client.post("/api/v1/chat", json=payload)
            self.assertEqual(
                response.status_code,
                400,
                f"Attempt {i} expected 400 Bad Request, got {response.status_code}"
            )

        # 11th request: Exceeded limit
        blocked = client.post("/api/v1/chat", json=payload)
        self.assertEqual(blocked.status_code, 429)
        data = blocked.json()
        self.assertEqual(data.get("error"), "RateLimitExceeded")
        self.assertIn("retry_after", data)
        self.assertIn("Retry-After", blocked.headers)
        print("  ✅ PASS: AI Chat rate limit (10/min) and HTTP 429 verified.")

    def test_dataset_upload_rate_limiting(self):
        """
        Verify POST /api/v1/admin/datasets/upload limits at 5 requests/min.
        """
        auth_headers = {"X-Admin-API-Key": settings.admin_api_key}

        # First 5 calls with invalid format are rejected with 400 (under limit)
        for i in range(1, 6):
            res = client.post(
                "/api/v1/admin/datasets/upload",
                headers=auth_headers,
                files={"file": ("bad.xyz", b"content", "text/plain")}
            )
            self.assertEqual(res.status_code, 400)

        # 6th call hits rate limit -> 429
        blocked = client.post(
            "/api/v1/admin/datasets/upload",
            headers=auth_headers,
            files={"file": ("bad.xyz", b"content", "text/plain")}
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["error"], "RateLimitExceeded")
        self.assertIn("Retry-After", blocked.headers)
        print("  ✅ PASS: Dataset upload rate limit (5/min) verified.")

    def test_dataset_process_and_import_rate_limiting(self):
        """
        Verify POST /api/v1/admin/datasets/{id}/process and /import are rate limited at 5/min.
        """
        auth_headers = {"X-Admin-API-Key": settings.admin_api_key}
        dummy_id = "00000000-0000-0000-0000-000000000000"

        # 1. Process endpoint
        for _ in range(5):
            res = client.post(f"/api/v1/admin/datasets/{dummy_id}/process", headers=auth_headers)
            self.assertEqual(res.status_code, 404)

        blocked_proc = client.post(f"/api/v1/admin/datasets/{dummy_id}/process", headers=auth_headers)
        self.assertEqual(blocked_proc.status_code, 429)
        self.assertEqual(blocked_proc.json()["error"], "RateLimitExceeded")

        # Reset limiter for import test
        limiter.reset()

        # 2. Import endpoint
        for _ in range(5):
            res = client.post(f"/api/v1/admin/datasets/{dummy_id}/import", headers=auth_headers)
            self.assertEqual(res.status_code, 404)

        blocked_imp = client.post(f"/api/v1/admin/datasets/{dummy_id}/import", headers=auth_headers)
        self.assertEqual(blocked_imp.status_code, 429)
        self.assertEqual(blocked_imp.json()["error"], "RateLimitExceeded")
        print("  ✅ PASS: Dataset process & import endpoints (5/min) verified.")

    def test_public_catalog_rate_limiting(self):
        """
        Verify GET /api/v1/datasets/catalog allows 60 requests/min and blocks on 61st.
        """
        for i in range(1, 61):
            res = client.get("/api/v1/datasets/catalog")
            self.assertEqual(res.status_code, 200, f"Request {i} failed with {res.status_code}")

        # 61st request
        blocked = client.get("/api/v1/datasets/catalog")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["error"], "RateLimitExceeded")
        self.assertIn("Retry-After", blocked.headers)
        print("  ✅ PASS: Public catalog rate limit (60/min) verified.")

    def test_health_check_unlimited(self):
        """
        Verify GET /api/v1/health is NOT rate limited by wildcard rules.
        """
        for _ in range(70):
            res = client.get("/api/v1/health")
            self.assertEqual(res.status_code, 200)
        print("  ✅ PASS: Health check endpoint has no unintended rate limit restrictions.")

    def test_valid_auth_workflow_under_limit(self):
        """
        Verify normal valid login and authenticated requests succeed under limit.
        """
        res = client.post(
            "/api/v1/admin/auth/login",
            json={"username": settings.admin_username, "password": settings.admin_password}
        )
        self.assertEqual(res.status_code, 200)
        token = res.json().get("access_token")
        self.assertIsNotNone(token)

        # Authenticated call to list datasets
        list_res = client.get("/api/v1/admin/datasets", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(list_res.status_code, 200)
        print("  ✅ PASS: Normal authenticated administrative operations function under limit.")

    def test_sql_validator_security_invariants(self):
        """
        Ensure SQL injection guardrails remain 100% effective and unaffected by rate limiting.
        """
        dangerous_queries = [
            "DROP TABLE users;",
            "SELECT * FROM users; DROP TABLE orders;",
            "INSERT INTO departments (name) VALUES ('Hacked');",
            "UPDATE employees SET salary = 999999;",
            "DELETE FROM products WHERE id = 1;",
            "ALTER TABLE users ADD COLUMN is_admin BOOLEAN;",
            "TRUNCATE TABLE students;",
            "SELECT pg_sleep(10);",
            "SELECT pg_terminate_backend(1234);",
            "/* comment */ DROP TABLE users;",
        ]
        for q in dangerous_queries:
            is_valid, msg = validate_sql(q)
            self.assertFalse(is_valid, f"Dangerous query unexpectedly allowed: {q}")
            self.assertIn("Security Error", msg)
        print("  ✅ PASS: SQL Security Validator invariants verified (100% blocked).")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  🚀 RUNNING ZERO-SQL AI V2 RATE LIMITING TEST SUITE")
    print("=" * 70 + "\n")
    unittest.main(verbosity=2)
