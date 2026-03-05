-- =============================================================
-- Runs ONCE during first-time PostgreSQL container initialisation.
-- Ensures the "admin" role has the correct scram-sha-256 password
-- hash so remote connections (from the Odoo container) succeed.
-- =============================================================

-- Re-set the password — this is idempotent and safe.
ALTER ROLE admin WITH LOGIN SUPERUSER PASSWORD '1234';
