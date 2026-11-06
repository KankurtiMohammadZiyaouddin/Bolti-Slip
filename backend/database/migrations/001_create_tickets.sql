-- backend/database/migrations/001_create_tickets.sql
-- Initial schema for Bolti Slip.
-- All ALTER TABLE statements use IF NOT EXISTS / OR IGNORE so re-running is safe.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tickets (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number      TEXT    NOT NULL UNIQUE,          -- BLT-0001
    customer_name      TEXT,
    customer_phone     TEXT,
    device_description TEXT    NOT NULL,                 -- transcribed complaint
    transcript_raw     TEXT,                             -- original STT transcript
    status             TEXT    NOT NULL DEFAULT 'open',  -- open | in_progress | resolved | closed
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Auto-update updated_at on every UPDATE
CREATE TRIGGER IF NOT EXISTS tickets_updated_at
    AFTER UPDATE ON tickets
    FOR EACH ROW
BEGIN
    UPDATE tickets SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = OLD.id;
END;
