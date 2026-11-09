-- backend/database/migrations/003_add_auth_and_customers.sql
-- Adds shops, customers, and sessions tables for multi-shop authentication.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shops (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    shop_name     TEXT NOT NULL,
    owner_name    TEXT NOT NULL,
    phone         TEXT,
    branch        TEXT DEFAULT 'Main Branch',
    address       TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TRIGGER IF NOT EXISTS shops_updated_at
    AFTER UPDATE ON shops
    FOR EACH ROW
BEGIN
    UPDATE shops SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id         INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    phone           TEXT NOT NULL,
    alternate_phone TEXT,
    email           TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CONSTRAINT uq_shop_customer UNIQUE (shop_id, phone)
);

CREATE TRIGGER IF NOT EXISTS customers_updated_at
    AFTER UPDATE ON customers
    FOR EACH ROW
BEGIN
    UPDATE customers SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = OLD.id;
END;

CREATE INDEX IF NOT EXISTS idx_customers_shop_phone ON customers(shop_id, phone);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    shop_id    INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_shop ON sessions(shop_id);
