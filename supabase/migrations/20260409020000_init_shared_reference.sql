-- ============================================================
-- AEGIS - official migration: shared reference tables
-- Source draft: supabase/drafts/reference-shared-draft.sql
--
-- Scope:
--   - currencies
--   - asset_classes
--
-- Notes:
--   - These tables are intentionally global shared references.
--   - They are not tenant-scoped.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- CURRENCIES
-- ============================================================

CREATE TABLE IF NOT EXISTS currencies (

    id_ccy          BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    code            TEXT        NOT NULL,
    name            TEXT        NOT NULL,
    symbol          TEXT,
    iso_numeric     SMALLINT,
    decimals        SMALLINT    NOT NULL DEFAULT 2 CHECK (decimals BETWEEN 0 AND 8),

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order      INTEGER     NOT NULL DEFAULT 100,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_currency_code_upper CHECK (code = UPPER(code)),

    UNIQUE (uuid),
    UNIQUE (code),
    UNIQUE (iso_numeric)

);

CREATE INDEX IF NOT EXISTS idx_currencies_active ON currencies(is_active);
CREATE INDEX IF NOT EXISTS idx_currencies_sort_order ON currencies(sort_order);


-- ============================================================
-- ASSET CLASSES
-- ============================================================

CREATE TABLE IF NOT EXISTS asset_classes (

    id_ac           BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    code            TEXT        NOT NULL,
    ice_code        TEXT,

    name            TEXT        NOT NULL,
    description     TEXT,

    sort_order      INTEGER     NOT NULL DEFAULT 100,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_asset_class_code_upper CHECK (code = UPPER(code)),

    UNIQUE (uuid),
    UNIQUE (code),
    UNIQUE (name),
    UNIQUE (ice_code)

);

CREATE INDEX IF NOT EXISTS idx_asset_classes_active ON asset_classes(is_active);
CREATE INDEX IF NOT EXISTS idx_asset_classes_ice_code ON asset_classes(ice_code);
CREATE INDEX IF NOT EXISTS idx_asset_classes_sort_order ON asset_classes(sort_order);


-- ============================================================
-- COUNTRIES (for future use, not yet seeded)
-- ============================================================

