-- Least-privilege PostgreSQL runtime-role template.
-- Run manually as a database administrator after setting psql variables:
--   psql -d telecom_db \
--     -v runtime_role='telecom_app_runtime' \
--     -v runtime_password='a-secret-from-your-password-manager' \
--     -f docs/db/postgresql-runtime-role.sql
-- Never commit the supplied password or place it in shell history in production.

\if :{?runtime_role}
\else
  \echo 'runtime_role is required'
  \quit 1
\endif

\if :{?runtime_password}
\else
  \echo 'runtime_password is required'
  \quit 1
\endif

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'runtime_role', :'runtime_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'runtime_role')
\gexec

SELECT format('ALTER ROLE %I NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION', :'runtime_role')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'runtime_role')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'runtime_role')
\gexec
SELECT format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I', :'runtime_role')
\gexec
SELECT format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO %I', :'runtime_role')
\gexec

-- Keep schema migration authority separate from the runtime role.
SELECT format('REVOKE CREATE ON SCHEMA public FROM %I', :'runtime_role')
\gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I', :'runtime_role')
\gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO %I', :'runtime_role')
\gexec
