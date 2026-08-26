"""
ZeroSQL AI V2 — Database Connection Pooling Verification Test Suite
Tests:
A. Pool initialization (idempotent, correct parameters)
B. Read-only pool acquisition
C. conn.read_only == True enforcement
D. Admin pool is write-capable (read_only == False)
E. Read/admin pools are completely separate instances
F. Connection is safely returned to pool on block exit
G. Read transaction rollback is always executed on block exit
H. Admin transaction rollback on exception and uncommitted state
I. Pool exhaustion timeout behavior (raises ConnectionError, no leak)
J. Pool shutdown (graceful closure of all pools)
K. Repeated init/close does not leak pools (idempotence)
L. Existing get_readonly_db_connection() API works with context manager & direct access
M. Existing get_admin_db_connection() API works with context manager & direct access
N. Fallback DirectConnectionContext works when pools are uninitialized
O. Connection URL hardening (connect_timeout & sslmode deduplication)
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import PoolTimeout

import database
from database import (
    init_db_pools,
    close_db_pools,
    get_pool_status,
    get_readonly_db_connection,
    get_admin_db_connection,
    get_db_connection,
    _harden_connection_url,
    PooledConnectionContext,
    DirectConnectionContext
)


class MockTransactionInfo:
    """Simulates PostgreSQL transaction status."""
    def __init__(self):
        self.transaction_status = psycopg.pq.TransactionStatus.IDLE


class FakeConnection:
    """Fake psycopg Connection for hermetic testing."""
    def __init__(self, name="fake_conn"):
        self.name = name
        self.read_only = False
        self.closed = False
        self.info = MockTransactionInfo()
        self.rollback_count = 0
        self.commit_count = 0

    def rollback(self):
        self.rollback_count += 1
        self.info.transaction_status = psycopg.pq.TransactionStatus.IDLE

    def commit(self):
        self.commit_count += 1
        self.info.transaction_status = psycopg.pq.TransactionStatus.IDLE

    def cursor(self):
        return MagicMock()

    def close(self):
        self.closed = True


class FakeConnectionPool:
    """Fake ConnectionPool simulating psycopg_pool.ConnectionPool."""
    def __init__(self, name="fake_pool", min_size=2, max_size=8, timeout=10.0):
        self.name = name
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout
        self.closed = False
        self.checked_out = 0
        self.returned = 0
        self.force_timeout = False

    def getconn(self, timeout=None):
        if self.force_timeout:
            raise PoolTimeout(f"Pool {self.name} timed out after {timeout}s")
        self.checked_out += 1
        conn = FakeConnection(name=f"conn_from_{self.name}")
        return conn

    def putconn(self, conn):
        self.checked_out -= 1
        self.returned += 1

    def close(self, timeout=5.0):
        self.closed = True


class TestDatabaseConnectionPooling(unittest.TestCase):
    """Hermetic unit tests for database connection pooling layer."""

    def setUp(self):
        """Ensure clean pool state before every test."""
        close_db_pools()

    def tearDown(self):
        """Clean up pools after every test."""
        close_db_pools()

    def test_O_connection_url_hardening(self):
        """Verify _harden_connection_url appends connect_timeout and sslmode without duplication."""
        # 1. Plain URL without params
        u1 = "postgresql://user:pass@localhost:5432/zerosql"
        h1 = _harden_connection_url(u1, connect_timeout=10, sslmode="require")
        self.assertIn("connect_timeout=10", h1)
        self.assertIn("sslmode=require", h1)

        # 2. URL already having connect_timeout=5
        u2 = "postgresql://user:pass@localhost:5432/zerosql?connect_timeout=5"
        h2 = _harden_connection_url(u2, connect_timeout=10, sslmode="require")
        self.assertIn("connect_timeout=5", h2)
        self.assertNotIn("connect_timeout=10", h2)  # Preserved existing value
        self.assertIn("sslmode=require", h2)

        # 3. URL already having sslmode=disable
        u3 = "postgresql://user:pass@localhost:5432/zerosql?sslmode=disable"
        h3 = _harden_connection_url(u3, connect_timeout=10, sslmode="require")
        self.assertIn("sslmode=disable", h3)
        self.assertNotIn("sslmode=require", h3)  # Preserved existing value
        self.assertIn("connect_timeout=10", h3)
        print("  ✅ PASS: O. Connection URL hardening and deduplication verified.")

    def test_A_pool_initialization(self):
        """Verify init_db_pools creates both pools with correct configurations."""
        with patch("database.ConnectionPool", side_effect=lambda **kwargs: FakeConnectionPool(
            name=kwargs.get("name"),
            min_size=kwargs.get("min_size"),
            max_size=kwargs.get("max_size"),
            timeout=kwargs.get("timeout")
        )):
            init_db_pools(
                min_size_ro=2,
                max_size_ro=8,
                min_size_admin=1,
                max_size_admin=4,
                timeout=10.0
            )

            status = get_pool_status()
            self.assertIsNotNone(status["readonly_pool"])
            self.assertEqual(status["readonly_pool"]["name"], "zerosql-readonly-pool")
            self.assertEqual(status["readonly_pool"]["min_size"], 2)
            self.assertEqual(status["readonly_pool"]["max_size"], 8)

            self.assertIsNotNone(status["admin_pool"])
            self.assertEqual(status["admin_pool"]["name"], "zerosql-admin-pool")
            self.assertEqual(status["admin_pool"]["min_size"], 1)
            self.assertEqual(status["admin_pool"]["max_size"], 4)
        print("  ✅ PASS: A. Pool initialization verified with exact parameters.")

    def test_B_and_C_readonly_pool_acquisition_and_isolation(self):
        """Verify read-only pool checkout enforces conn.read_only == True."""
        fake_ro_pool = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        database._readonly_pool = fake_ro_pool

        with get_readonly_db_connection() as conn:
            self.assertTrue(conn.read_only)
            self.assertEqual(fake_ro_pool.checked_out, 1)

        # Connection returned to pool
        self.assertEqual(fake_ro_pool.checked_out, 0)
        self.assertEqual(fake_ro_pool.returned, 1)
        print("  ✅ PASS: B & C. Read-only acquisition and conn.read_only=True verified.")

    def test_D_admin_pool_write_capability(self):
        """Verify admin pool checkout preserves write-capability (read_only == False)."""
        fake_admin_pool = FakeConnectionPool("zerosql-admin-pool", 1, 4)
        database._admin_pool = fake_admin_pool

        with get_admin_db_connection() as conn:
            self.assertFalse(conn.read_only)
            self.assertEqual(fake_admin_pool.checked_out, 1)

        self.assertEqual(fake_admin_pool.checked_out, 0)
        self.assertEqual(fake_admin_pool.returned, 1)
        print("  ✅ PASS: D. Admin pool write-capability verified.")

    def test_E_read_and_admin_pools_are_separate(self):
        """Verify read-only and admin pools are strictly separate instances."""
        fake_ro = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        fake_admin = FakeConnectionPool("zerosql-admin-pool", 1, 4)
        database._readonly_pool = fake_ro
        database._admin_pool = fake_admin

        self.assertIsNot(fake_ro, fake_admin)
        self.assertNotEqual(fake_ro.name, fake_admin.name)

        # Check out from read
        with get_readonly_db_connection() as conn_ro:
            self.assertEqual(fake_ro.checked_out, 1)
            self.assertEqual(fake_admin.checked_out, 0)

        # Check out from admin
        with get_admin_db_connection() as conn_admin:
            self.assertEqual(fake_ro.checked_out, 0)
            self.assertEqual(fake_admin.checked_out, 1)

        self.assertEqual(fake_ro.checked_out, 0)
        self.assertEqual(fake_admin.checked_out, 0)
        print("  ✅ PASS: E. Read and Admin pools strictly separated.")

    def test_F_and_G_read_transaction_rollback_and_return(self):
        """Verify read-only transactions are always rolled back on return."""
        fake_ro = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        database._readonly_pool = fake_ro

        captured_conn = None
        with get_readonly_db_connection() as conn:
            captured_conn = conn
            self.assertEqual(captured_conn.rollback_count, 0)

        # Exited block: rollback called and connection returned
        self.assertEqual(captured_conn.rollback_count, 1)
        self.assertEqual(fake_ro.returned, 1)
        print("  ✅ PASS: F & G. Read transaction rollback & safe return verified.")

    def test_H_admin_transaction_rollback_on_exception(self):
        """Verify admin transactions roll back on exception and uncommitted state."""
        fake_admin = FakeConnectionPool("zerosql-admin-pool", 1, 4)
        database._admin_pool = fake_admin

        # 1. Exception raised inside block -> must rollback
        captured_conn = None
        with self.assertRaises(ValueError):
            with get_admin_db_connection() as conn:
                captured_conn = conn
                conn.info.transaction_status = psycopg.pq.TransactionStatus.INERROR
                raise ValueError("Simulated business error")

        self.assertEqual(captured_conn.rollback_count, 1)
        self.assertEqual(fake_admin.returned, 1)

        # 2. Uncommitted transaction left in progress -> must rollback on exit
        with get_admin_db_connection() as conn:
            captured_conn_2 = conn
            conn.info.transaction_status = psycopg.pq.TransactionStatus.INTRANS

        self.assertEqual(captured_conn_2.rollback_count, 1)
        self.assertEqual(fake_admin.returned, 2)

        # 3. Explicitly committed transaction -> does not rollback
        with get_admin_db_connection() as conn:
            captured_conn_3 = conn
            conn.commit()

        self.assertEqual(captured_conn_3.commit_count, 1)
        self.assertEqual(captured_conn_3.rollback_count, 0)
        print("  ✅ PASS: H. Admin transaction rollback on exception & uncommitted state verified.")

    def test_I_pool_exhaustion_timeout_behavior(self):
        """Verify PoolTimeout triggers clean ConnectionError without resource leaks."""
        fake_ro = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        fake_ro.force_timeout = True
        database._readonly_pool = fake_ro

        with self.assertRaises(ConnectionError) as ctx:
            with get_readonly_db_connection():
                pass

        self.assertIn("pool exhausted", str(ctx.exception).lower())
        self.assertEqual(fake_ro.checked_out, 0)
        print("  ✅ PASS: I. Pool exhaustion timeout behavior verified.")

    def test_J_and_K_pool_shutdown_and_idempotence(self):
        """Verify pool shutdown and repeated init/close idempotence."""
        fake_ro = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        fake_admin = FakeConnectionPool("zerosql-admin-pool", 1, 4)
        database._readonly_pool = fake_ro
        database._admin_pool = fake_admin

        # Close pools
        close_db_pools()
        self.assertTrue(fake_ro.closed)
        self.assertTrue(fake_admin.closed)
        self.assertIsNone(database._readonly_pool)
        self.assertIsNone(database._admin_pool)

        # Second close must not raise errors (idempotent)
        close_db_pools()

        # Idempotent init: if already set, does not replace
        database._readonly_pool = fake_ro
        database._admin_pool = fake_admin
        init_db_pools()
        self.assertIs(database._readonly_pool, fake_ro)
        print("  ✅ PASS: J & K. Pool shutdown and idempotence verified.")

    def test_L_and_M_existing_apis_compatibility(self):
        """Verify both context manager and direct access patterns work on existing APIs."""
        fake_ro = FakeConnectionPool("zerosql-readonly-pool", 2, 8)
        fake_admin = FakeConnectionPool("zerosql-admin-pool", 1, 4)
        database._readonly_pool = fake_ro
        database._admin_pool = fake_admin

        # Pattern 1: get_readonly_db_connection direct access
        conn1 = get_readonly_db_connection()
        self.assertTrue(conn1.read_only)
        self.assertEqual(fake_ro.checked_out, 1)
        conn1.close()
        self.assertEqual(fake_ro.checked_out, 0)

        # Pattern 2: get_admin_db_connection direct access
        conn2 = get_admin_db_connection()
        self.assertFalse(conn2.read_only)
        self.assertEqual(fake_admin.checked_out, 1)
        conn2.close()
        self.assertEqual(fake_admin.checked_out, 0)

        # Pattern 3: get_db_connection dispatch wrapper
        with get_db_connection(readonly=True) as ro_c:
            self.assertTrue(ro_c.read_only)
        with get_db_connection(readonly=False) as adm_c:
            self.assertFalse(adm_c.read_only)
        print("  ✅ PASS: L & M. Existing API compatibility (context manager + direct) verified.")

    def test_N_direct_connection_fallback_when_uninitialized(self):
        """Verify direct connection fallback works cleanly when pools are None."""
        database._readonly_pool = None
        database._admin_pool = None

        mock_conn = FakeConnection("fallback_conn")
        with patch("psycopg.connect", return_value=mock_conn):
            with get_readonly_db_connection() as conn:
                self.assertTrue(conn.read_only)

            self.assertTrue(mock_conn.closed)
            self.assertEqual(mock_conn.rollback_count, 1)
        print("  ✅ PASS: N. Direct connection fallback when pools are uninitialized verified.")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  🚀 RUNNING ZERO-SQL AI V2 CONNECTION POOLING TEST SUITE")
    print("=" * 70 + "\n")
    unittest.main(verbosity=2)
