-- Read-only role for the dashboard agent.
--
-- The agent NEVER connects as the owner. It connects as dashboard_readonly,
-- which can only SELECT. This is the last line of defense behind sql_guard.py:
-- even if a malicious/hallucinated query slips past the application-level
-- guard, the database itself will reject any write/DDL.
--
-- Applied on first container start. The password is intentionally simple for a
-- local prototype; in production this would come from a secret manager.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dashboard_readonly') THEN
        CREATE ROLE dashboard_readonly LOGIN PASSWORD 'readonly_pw';
    END IF;
END
$$;

-- Connect + read the public schema, nothing else.
GRANT CONNECT ON DATABASE dashboard TO dashboard_readonly;
GRANT USAGE ON SCHEMA public TO dashboard_readonly;

-- SELECT on everything that exists now and anything created later.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dashboard_readonly;

-- Explicitly make sure the role can never write.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM dashboard_readonly;
