-- ==============================================================================
-- Dedicated PostgreSQL Read-Only Role Configuration for AI SQL Agent
-- ==============================================================================
-- This script creates a secure, dedicated read-only database user for the AI agent.
-- Run this script as the PostgreSQL superuser (e.g. 'postgres').

-- 1. Create a dedicated read-only user
-- Replace 'YourStrongPasswordHere123!' with your desired secure password
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sql_agent_readonly') THEN
      CREATE USER sql_agent_readonly WITH PASSWORD 'YourStrongPasswordHere123!';
   END IF;
END
$$;

-- 2. Connect to the application database (ai_sql_agent)
-- \c ai_sql_agent

-- 3. Grant basic connection permission to the database
GRANT CONNECT ON DATABASE ai_sql_agent TO sql_agent_readonly;

-- 4. Grant schema usage
GRANT USAGE ON SCHEMA public TO sql_agent_readonly;

-- 5. Grant SELECT permission ONLY on all existing tables in public schema
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_agent_readonly;

-- 6. Ensure future tables also automatically get SELECT permission only
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_agent_readonly;

-- 7. Explicitly REVOKE any write or administrative privileges
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM sql_agent_readonly;
REVOKE CREATE ON SCHEMA public FROM sql_agent_readonly;

-- 8. Enforce read-only transaction mode at the database user level
ALTER USER sql_agent_readonly SET default_transaction_read_only = on;

-- ==============================================================================
-- Configuration in .env:
-- Update your .env file to use this read-only user for the AI agent:
-- DATABASE_URL="postgresql://sql_agent_readonly:YourStrongPasswordHere123!@localhost:5432/ai_sql_agent"
-- ==============================================================================
