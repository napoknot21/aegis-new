-- ============================================================
-- AEGIS - official migration: shared reference tables
-- Source draft: supabase/drafts/reference-shared-draft.sql
--
-- Scope:
--   - currencies
--   - asset_classes
--   - countries
--   - cities
--   - fx_rates
--   - quotes
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
-- COUNTRIES
-- ============================================================

CREATE TABLE IF NOT EXISTS countries (

    id_country     BIGSERIAL   PRIMARY KEY,
    uuid           UUID        NOT NULL DEFAULT uuid_generate_v4(),

    iso2           TEXT        NOT NULL,
    iso3           TEXT,
    name           TEXT        NOT NULL,
    official_name  TEXT,

    region         TEXT,
    sub_region     TEXT,

    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order     INTEGER     NOT NULL DEFAULT 100,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_country_iso2_format CHECK (iso2 = UPPER(iso2) AND iso2 ~ '^[A-Z]{2}$'),
    CONSTRAINT chk_country_iso3_format CHECK (iso3 IS NULL OR (iso3 = UPPER(iso3) AND iso3 ~ '^[A-Z]{3}$')),

    UNIQUE (uuid),
    UNIQUE (iso2),
    UNIQUE (iso3),
    UNIQUE (name)

);

CREATE INDEX IF NOT EXISTS idx_countries_active ON countries(is_active);
CREATE INDEX IF NOT EXISTS idx_countries_region ON countries(region, sub_region);
CREATE INDEX IF NOT EXISTS idx_countries_sort_order ON countries(sort_order);


-- ============================================================
-- CITIES
-- ============================================================

CREATE TABLE IF NOT EXISTS cities (

    id_city       BIGSERIAL   PRIMARY KEY,
    uuid          UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_country    BIGINT      NOT NULL,

    name          TEXT        NOT NULL,
    ascii_name    TEXT,
    admin_area    TEXT,
    timezone_name TEXT,

    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order    INTEGER     NOT NULL DEFAULT 100,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_city_country FOREIGN KEY (id_country) REFERENCES countries(id_country),

    UNIQUE (uuid),
    UNIQUE NULLS NOT DISTINCT (id_country, name, admin_area)

);

CREATE INDEX IF NOT EXISTS idx_cities_country ON cities(id_country);
CREATE INDEX IF NOT EXISTS idx_cities_active ON cities(is_active);
CREATE INDEX IF NOT EXISTS idx_cities_timezone ON cities(timezone_name);
CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(id_country, name);


-- ============================================================
-- FX RATES
-- ============================================================

CREATE TABLE IF NOT EXISTS fx_rates (

    id_fx_rate  BIGSERIAL     PRIMARY KEY,
    uuid        UUID          NOT NULL DEFAULT uuid_generate_v4(),

    id_ccy_from BIGINT        NOT NULL,
    id_ccy_to   BIGINT        NOT NULL,

    rate_date   DATE          NOT NULL,
    rate        NUMERIC(18,8) NOT NULL,
    source      TEXT,

    loaded_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_fx_from FOREIGN KEY (id_ccy_from) REFERENCES currencies(id_ccy),
    CONSTRAINT fk_fx_to   FOREIGN KEY (id_ccy_to) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE NULLS NOT DISTINCT (id_ccy_from, id_ccy_to, rate_date, source)

);

CREATE INDEX IF NOT EXISTS idx_fx_rates_date ON fx_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_fx_rates_pair ON fx_rates(id_ccy_from, id_ccy_to);

COMMENT ON TABLE fx_rates IS
    'Global shared FX rate reference. No tenant boundary; provenance is captured in source.';


-- ============================================================
-- QUOTES
-- ============================================================

CREATE TABLE IF NOT EXISTS quotes (

    id_quote        BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    quote           TEXT        NOT NULL,
    author          TEXT        NOT NULL,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order      INTEGER     NOT NULL DEFAULT 100,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (uuid),
    UNIQUE (quote, author)

);

CREATE INDEX IF NOT EXISTS idx_quotes_active ON quotes(is_active);
CREATE INDEX IF NOT EXISTS idx_quotes_sort_order ON quotes(sort_order);
