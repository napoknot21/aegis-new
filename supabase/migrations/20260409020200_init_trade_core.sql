-- ============================================================
-- AEGIS - official migration: trade core
-- Source draft: supabase/drafts/core-schema-draft.sql
--
-- Scope:
--   - funds
--   - banks / counterparties
--   - books
--   - trade discretionary tables
--
-- Dependencies:
--   - organisations(id_org)
--   - currencies(id_ccy)
--   - offices(id_org, id_off)
--   - asset_classes(id_ac)
--   - users(id_org, id_user)
--
-- Notes:
--   - Tenant boundary = organisation.
--   - Shared reference tables like currencies and asset_classes remain global.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- FUNDS
-- ============================================================

CREATE TABLE IF NOT EXISTS funds (

    id_f            BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org          BIGINT      NOT NULL,
    id_ccy          BIGINT      NOT NULL,

    name            TEXT        NOT NULL,
    code            TEXT        NOT NULL,

    fund_type       TEXT        DEFAULT 'aif' CHECK (fund_type IN ('aif','ucits','amc','other')),
    inception_date  DATE,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_fund_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_fund_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_f),
    UNIQUE (id_org, code)

);
CREATE INDEX IF NOT EXISTS idx_funds_org ON funds(id_org);


CREATE TABLE IF NOT EXISTS fund_office_access (

    id          BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org      BIGINT      NOT NULL,
    id_f        BIGINT      NOT NULL,
    id_off      BIGINT      NOT NULL,

    access_type TEXT        NOT NULL DEFAULT 'primary' CHECK (access_type IN ('primary','secondary')),
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_foa_org    FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_foa_fund   FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_foa_office FOREIGN KEY (id_org, id_off) REFERENCES offices(id_org, id_off),

    UNIQUE (uuid),
    UNIQUE (id_org, id_f, id_off)
);
CREATE INDEX IF NOT EXISTS idx_foa_org ON fund_office_access(id_org);
CREATE INDEX IF NOT EXISTS idx_foa_fund ON fund_office_access(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_foa_office ON fund_office_access(id_org, id_off);


-- ============================================================
-- BANKS / COUNTERPARTIES
-- ============================================================

CREATE TABLE IF NOT EXISTS banks (

    id_bank     BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org      BIGINT      NOT NULL,

    name        TEXT        NOT NULL,
    code        TEXT        NOT NULL,

    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_bank_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_bank),
    UNIQUE (id_org, code)

);
CREATE INDEX IF NOT EXISTS idx_banks_org ON banks(id_org);

CREATE TABLE IF NOT EXISTS counterparties (

    id_ctpy         BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org          BIGINT      NOT NULL,

    id_bank         BIGINT,

    ice_name        TEXT,
    ext_code        TEXT,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_ctpy_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_ctpy_bank FOREIGN KEY (id_org, id_bank) REFERENCES banks(id_org, id_bank),

    UNIQUE (uuid),
    UNIQUE (id_org, id_ctpy),
    UNIQUE (id_org, ext_code)

);
CREATE INDEX IF NOT EXISTS idx_ctpy_org ON counterparties(id_org);
CREATE INDEX IF NOT EXISTS idx_ctpy_bank ON counterparties(id_org, id_bank);


-- ============================================================
-- BOOKS
-- ============================================================

CREATE TABLE IF NOT EXISTS books (

    id_book       BIGSERIAL   PRIMARY KEY,
    uuid          UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org        BIGINT      NOT NULL,
    name          TEXT        NOT NULL,
    id_f          BIGINT      NOT NULL,
    parent_id     BIGINT,

    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_book_org    FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_book_fund   FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_book_parent FOREIGN KEY (id_org, parent_id) REFERENCES books(id_org, id_book),

    UNIQUE (uuid),
    UNIQUE (id_org, id_book),
    UNIQUE (id_org, id_f, name)

);
CREATE INDEX IF NOT EXISTS idx_books_org ON books(id_org);
CREATE INDEX IF NOT EXISTS idx_books_fund ON books(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_books_parent ON books(id_org, parent_id);


-- ============================================================
-- TRADES
-- ============================================================

CREATE TABLE IF NOT EXISTS trade_types (

    id_type     BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org      BIGINT      NOT NULL,

    name        TEXT        NOT NULL,
    code        TEXT        NOT NULL,

    CONSTRAINT fk_trade_type_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_type),
    UNIQUE (id_org, code)

);
CREATE INDEX IF NOT EXISTS idx_trade_types_org ON trade_types(id_org);


CREATE TABLE IF NOT EXISTS trade_disc_labels (

    id_label    BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org      BIGINT      NOT NULL,

    code        TEXT        NOT NULL,

    CONSTRAINT fk_trade_label_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_label),
    UNIQUE (id_org, code)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_labels_org ON trade_disc_labels(id_org);


CREATE TABLE IF NOT EXISTS trade_spe (

    id_spe  BIGSERIAL   PRIMARY KEY,
    uuid    UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org  BIGINT      NOT NULL,

    CONSTRAINT fk_trade_spe_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_spe)

);
CREATE INDEX IF NOT EXISTS idx_trade_spe_org ON trade_spe(id_org);


CREATE TABLE IF NOT EXISTS trades (

    id_trade            BIGSERIAL   PRIMARY KEY,
    uuid                UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org              BIGINT      NOT NULL,

    id_spe              BIGINT      NOT NULL,
    id_type             BIGINT      NOT NULL,

    id_f                BIGINT      NOT NULL,

    booked_by           BIGINT,
    booked_at           TIMESTAMPTZ DEFAULT NOW(),

    last_modified_by    BIGINT,
    last_modified_at    TIMESTAMPTZ,

    status              TEXT        NOT NULL DEFAULT 'booked'
                        CHECK (status IN ('booked','recap_done','validated','rejected','cancelled')),

    CONSTRAINT fk_trade_org              FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_trade_spe              FOREIGN KEY (id_org, id_spe) REFERENCES trade_spe(id_org, id_spe),
    CONSTRAINT fk_trade_type             FOREIGN KEY (id_org, id_type) REFERENCES trade_types(id_org, id_type),
    CONSTRAINT fk_trade_fund             FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_trade_booked_by_user   FOREIGN KEY (id_org, booked_by) REFERENCES users(id_org, id_user),
    CONSTRAINT fk_trade_modified_by_user FOREIGN KEY (id_org, last_modified_by) REFERENCES users(id_org, id_user),

    UNIQUE (uuid),
    UNIQUE (id_org, id_trade),
    UNIQUE (id_spe)

);
CREATE INDEX IF NOT EXISTS idx_trades_org ON trades(id_org);
CREATE INDEX IF NOT EXISTS idx_trades_fund ON trades(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_trades_type ON trades(id_org, id_type);


CREATE TABLE IF NOT EXISTS trade_disc (

    id_spe              BIGINT      PRIMARY KEY,
    id_org              BIGINT      NOT NULL,

    id_book             BIGINT      NOT NULL,
    id_portfolio        BIGINT,

    id_ctpy             BIGINT      NOT NULL,
    id_label            BIGINT      NOT NULL,

    ice_trade_id        TEXT,
    external_id         TEXT,

    description         TEXT,
    trade_name          TEXT,
    trade_date          DATE,

    creation_time       TIMESTAMPTZ,
    last_update_time    TIMESTAMPTZ,

    volume              INTEGER,

    ice_status          TEXT CHECK (ice_status IN ('Success','Failed')),
    originating_action  TEXT CHECK (originating_action IN ('New','Exercise','Amendment','Early termination')),

    CONSTRAINT fk_disc_org       FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_disc_spe       FOREIGN KEY (id_org, id_spe) REFERENCES trade_spe(id_org, id_spe),
    CONSTRAINT fk_disc_book      FOREIGN KEY (id_org, id_book) REFERENCES books(id_org, id_book),
    CONSTRAINT fk_disc_portfolio FOREIGN KEY (id_org, id_portfolio) REFERENCES books(id_org, id_book),
    CONSTRAINT fk_disc_ctpy      FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),
    CONSTRAINT fk_disc_label     FOREIGN KEY (id_org, id_label) REFERENCES trade_disc_labels(id_org, id_label),

    UNIQUE (id_org, id_spe)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_org ON trade_disc(id_org);
CREATE INDEX IF NOT EXISTS idx_trade_disc_book ON trade_disc(id_org, id_book);
CREATE INDEX IF NOT EXISTS idx_trade_disc_ctpy ON trade_disc(id_org, id_ctpy);
CREATE INDEX IF NOT EXISTS idx_trade_disc_label ON trade_disc(id_org, id_label);


-- ============================================================
-- TRADE CHILD TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS trade_disc_legs (

    id_leg      BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org      BIGINT      NOT NULL,

    id_disc     BIGINT      NOT NULL,
    id_ac       BIGINT      NOT NULL,
    leg_id      TEXT        NOT NULL,

    leg_code    TEXT,
    direction   TEXT        CHECK (direction IN ('Buy','Sell')),
    notional    NUMERIC(18,6),
    id_ccy      BIGINT,

    CONSTRAINT fk_leg_org  FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leg_disc FOREIGN KEY (id_org, id_disc) REFERENCES trade_disc(id_org, id_spe),
    CONSTRAINT fk_leg_ac   FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),
    CONSTRAINT fk_leg_ccy  FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leg),
    UNIQUE (id_org, id_disc, leg_id)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_org ON trade_disc_legs(id_org);
CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_disc ON trade_disc_legs(id_org, id_disc);
CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_ac ON trade_disc_legs(id_org, id_ac);


CREATE TABLE IF NOT EXISTS trade_disc_premiums (

    id_prem        BIGSERIAL   PRIMARY KEY,
    uuid           UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org         BIGINT      NOT NULL,

    id_leg         BIGINT      NOT NULL,

    amount         NUMERIC(18,6),

    id_ccy         BIGINT,
    p_date         DATE,

    markup         NUMERIC(18,6),
    total          NUMERIC(18,6),

    payload_json   JSONB,

    CONSTRAINT fk_prem_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_prem_leg FOREIGN KEY (id_org, id_leg) REFERENCES trade_disc_legs(id_org, id_leg),
    CONSTRAINT fk_prem_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leg)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_premiums_org ON trade_disc_premiums(id_org);

CREATE TABLE IF NOT EXISTS trade_disc_fields (

    id_field        BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org          BIGINT      NOT NULL,

    id_leg          BIGINT      NOT NULL,

    id_ccy          BIGINT,
    d_date          DATE,

    notional        NUMERIC(18,6),
    payout_ccy_id   BIGINT,
    buysell         TEXT,

    i_type          TEXT,

    CONSTRAINT fk_field_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_field_leg FOREIGN KEY (id_org, id_leg) REFERENCES trade_disc_legs(id_org, id_leg),
    CONSTRAINT fk_field_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),
    CONSTRAINT fk_field_payout_ccy FOREIGN KEY (payout_ccy_id) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leg)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_fields_org ON trade_disc_fields(id_org);

CREATE TABLE IF NOT EXISTS trade_disc_instruments (

    id_inst          BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org           BIGINT      NOT NULL,

    id_leg           BIGINT      NOT NULL,

    id_ac            BIGINT,

    notional         TEXT,
    id_ccy           BIGINT,

    buysell          TEXT  CHECK (buysell in ('Buy','Sell')),
    i_type           TEXT,

    trade_date       DATE,

    isin             TEXT,
    bbg_ticker       TEXT,

    payload_json     JSONB,

    CONSTRAINT fk_inst_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_inst_leg FOREIGN KEY (id_org, id_leg) REFERENCES trade_disc_legs(id_org, id_leg),
    CONSTRAINT fk_inst_ac  FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),
    CONSTRAINT fk_inst_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leg)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_instruments_org ON trade_disc_instruments(id_org);


CREATE TABLE IF NOT EXISTS trade_disc_settlements (

    id_settle      BIGSERIAL   PRIMARY KEY,
    uuid           UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org         BIGINT      NOT NULL,

    id_leg         BIGINT      NOT NULL,

    s_date         DATE,

    id_ccy         BIGINT,
    type           TEXT,

    payload_json   JSONB,

    CONSTRAINT fk_settle_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_settle_leg FOREIGN KEY (id_org, id_leg) REFERENCES trade_disc_legs(id_org, id_leg),
    CONSTRAINT fk_settle_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leg)

);
CREATE INDEX IF NOT EXISTS idx_trade_disc_settlements_org ON trade_disc_settlements(id_org);
