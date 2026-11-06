-- backend/database/migrations/002_add_ticket_fields.sql
-- Adds four product-required fields to the tickets table.
-- SQLite does not support IF NOT EXISTS on ALTER TABLE ADD COLUMN,
-- so db.py guards each statement by checking PRAGMA table_info first.

ALTER TABLE tickets ADD COLUMN reported_problem    TEXT;
ALTER TABLE tickets ADD COLUMN repair_instructions TEXT;
ALTER TABLE tickets ADD COLUMN expected_delivery   TEXT;
ALTER TABLE tickets ADD COLUMN estimated_cost      REAL;
