-- backend/database/migrations_pg/001_initial_schema.sql
-- Idempotent PostgreSQL schema definition for Bolti Slip.
-- Preserves all entities, constraints, foreign keys, indexes, and automatic updated_at timestamps.

-- 1. Shared Trigger Function for auto-updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Shops Table (Multi-tenant shopkeeper accounts)
CREATE TABLE IF NOT EXISTS shops (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50) NOT NULL,
    password_hash TEXT NOT NULL,
    shop_name     TEXT NOT NULL,
    owner_name    TEXT NOT NULL,
    phone         VARCHAR(30),
    branch        VARCHAR(100) DEFAULT 'Main Branch',
    address       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Case-insensitive unique index for username (matches SQLite COLLATE NOCASE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_shops_username_lower ON shops (LOWER(username));

DROP TRIGGER IF EXISTS trigger_shops_updated_at ON shops;
CREATE TRIGGER trigger_shops_updated_at
    BEFORE UPDATE ON shops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id              BIGSERIAL PRIMARY KEY,
    shop_id         BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    phone           VARCHAR(30) NOT NULL,
    alternate_phone VARCHAR(30),
    email           VARCHAR(255),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_shop_customer UNIQUE (shop_id, phone)
);

CREATE INDEX IF NOT EXISTS idx_customers_shop_phone ON customers(shop_id, phone);

DROP TRIGGER IF EXISTS trigger_customers_updated_at ON customers;
CREATE TRIGGER trigger_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 4. Tickets Table (Repair tickets scoped by shop_id and customer_id)
CREATE TABLE IF NOT EXISTS tickets (
    id                  BIGSERIAL PRIMARY KEY,
    ticket_number       VARCHAR(32) NOT NULL UNIQUE,
    shop_id             BIGINT REFERENCES shops(id) ON DELETE SET NULL,
    customer_id         BIGINT REFERENCES customers(id) ON DELETE SET NULL,
    customer_name       TEXT,
    customer_phone      VARCHAR(30),
    device_description  TEXT NOT NULL,
    transcript_raw      TEXT,
    status              VARCHAR(32) NOT NULL DEFAULT 'open',
    reported_problem    TEXT,
    repair_instructions TEXT,
    expected_delivery   TEXT,
    estimated_cost      NUMERIC(10, 2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_shop ON tickets(shop_id);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id);

DROP TRIGGER IF EXISTS trigger_tickets_updated_at ON tickets;
CREATE TRIGGER trigger_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 5. Sessions Table (Token-based shopkeeper sessions)
CREATE TABLE IF NOT EXISTS sessions (
    token      VARCHAR(64) PRIMARY KEY,
    shop_id    BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_shop ON sessions(shop_id);
