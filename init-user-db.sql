-- =============================================================
-- Runs ONCE during first-time PostgreSQL container initialisation.
-- Ensures the "odoo" role has the correct scram-sha-256 password
-- hash so remote connections (from the Odoo container) succeed.
-- =============================================================

-- Re-set the password — this is idempotent and safe.
ALTER ROLE odoo WITH LOGIN SUPERUSER PASSWORD 'odoo_password';
