-- ============================================================
-- AEGIS - official migration: reporting snapshots
-- Source draft: supabase/drafts/core-schema-draft.sql
--
-- Scope:
--   - simm_snapshots
--   - simm_snapshot_rows

--   - expiries_snapshots
--   - expiries

--   - nav_estimated_snapshots
--   - nav_estimated

--   - leverages_snapshots
--   - leverages

--   - leverages_per_underlying_snapshots
--   - leverages_per_underlying

--   - long_short_delta_snapshots
--   - long_short_delta

--   - counterparty_concentration_snapshots
--   - counterparty_concentration

--   - leverages_per_trade_snapshots
--   - leverages_per_trade
--
-- Dependencies:
--   - organisations(id_org)
--   - currencies(id_ccy)
--   - asset_classes(id_ac)
--   - funds(id_org, id_f)
--   - counterparties(id_org, id_ctpy)
--
-- Notes:
--   - Tenant boundary = organisation.
--   - Snapshot tables are tenant-scoped and fund-scoped.
--   - ingestion_runs links the intraday reporting families in a later migration; SIMM stays daily and independent.
--   - simm_snapshots.id_run remains a daily source-side load reference and is not linked to ingestion_runs.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- SIMM
-- ============================================================

CREATE TABLE IF NOT EXISTS simm_snapshots (

    id_simm_snapshot    BIGSERIAL   PRIMARY KEY,
    uuid                UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org              BIGINT      NOT NULL,

    id_run              BIGINT      NOT NULL,
    id_f                BIGINT      NOT NULL,

    as_of_date          DATE        NOT NULL,
    source_name         TEXT        NOT NULL DEFAULT 'libapi',

    source_file_name    TEXT,

    source_generated_at TIMESTAMPTZ,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status              TEXT        NOT NULL DEFAULT 'loaded'
                        CHECK (status IN ('loaded','validated','official','replaced','failed')),

    row_count           INTEGER     NOT NULL DEFAULT 0,
    is_official         BOOLEAN     NOT NULL DEFAULT FALSE,

    notes               TEXT,
    CONSTRAINT fk_simm_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_simm_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    UNIQUE (uuid),
    UNIQUE (id_org, id_simm_snapshot),
    UNIQUE (id_org, id_f, as_of_date, is_official)
);
CREATE INDEX IF NOT EXISTS idx_simm_snapshots_org ON simm_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_simm_snapshots_fund ON simm_snapshots(id_org, id_f);

CREATE TABLE IF NOT EXISTS simm_snapshot_rows (

    id_simm_row        BIGSERIAL   PRIMARY KEY,
    uuid               UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org             BIGINT      NOT NULL,

    id_simm_snapshot   BIGINT      NOT NULL,
    id_f               BIGINT      NOT NULL,

    as_of_date         DATE        NOT NULL,

    id_ctpy            BIGINT,
    counterparty_raw   TEXT        NOT NULL,

    im_value           NUMERIC(18,6) NOT NULL,
    mv_value           NUMERIC(18,6),

    mv_capped_value    NUMERIC(18,6),
    capped_type        TEXT,

    net_margin_value   NUMERIC(18,6),

    raw_payload_json   JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_simm_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_simm_row_snapshot FOREIGN KEY (id_org, id_simm_snapshot)
        REFERENCES simm_snapshots(id_org, id_simm_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_simm_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_simm_row_ctpy FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_simm_snapshot, counterparty_raw)

);
CREATE INDEX IF NOT EXISTS idx_simm_snapshot_rows_org ON simm_snapshot_rows(id_org);
CREATE INDEX IF NOT EXISTS idx_simm_snapshot_rows_snapshot ON simm_snapshot_rows(id_org, id_simm_snapshot);
CREATE INDEX IF NOT EXISTS idx_simm_snapshot_rows_fund ON simm_snapshot_rows(id_org, id_f);


-- ============================================================
-- EXPIRIES
-- ============================================================

CREATE TABLE IF NOT EXISTS expiries_snapshots (

    id_exp_snapshot    BIGSERIAL   PRIMARY KEY,
    uuid               UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org             BIGINT      NOT NULL,

    id_run             BIGINT      NOT NULL,
    id_f               BIGINT      NOT NULL,

    snapshot_date      DATE        NOT NULL,
    snapshot_ts        TIMESTAMPTZ NOT NULL,

    file_name          TEXT        NOT NULL,
    file_path          TEXT,

    file_checksum      TEXT,

    imported_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    row_count          INTEGER     NOT NULL DEFAULT 0,

    is_latest_for_day  BOOLEAN     NOT NULL DEFAULT FALSE,
    status             TEXT        NOT NULL DEFAULT 'loaded'
                        CHECK (status IN ('loaded','validated','official','replaced','failed')),
    notes              TEXT,
    CONSTRAINT fk_exp_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_exp_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    UNIQUE (uuid),
    UNIQUE (id_org, id_exp_snapshot),
    UNIQUE (id_org, id_f, snapshot_ts)

);
CREATE INDEX IF NOT EXISTS idx_expiries_snapshots_org ON expiries_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_expiries_snapshots_fund ON expiries_snapshots(id_org, id_f);


CREATE TABLE IF NOT EXISTS expiries (

    id_exp_row          BIGSERIAL   PRIMARY KEY,
    uuid                UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org              BIGINT      NOT NULL,

    id_exp_snapshot     BIGINT      NOT NULL,

    trade_type          TEXT,
    underlying_asset    TEXT,
    termination_date    DATE,

    buy_sell            TEXT       CHECK (buy_sell IN ('Buy','Sell', 'Receive', 'Pay')),
    notional            NUMERIC(18,6),
    portfolio_name      TEXT,
    id_ac               BIGINT,
    call_put            TEXT      CHECK (call_put IN ('Call','Put')),
    strike              NUMERIC(18,6),
    trigger_value       NUMERIC(18,6),
    reference_spot      NUMERIC(18,6),
    id_ctpy             BIGINT,
    mv_value            NUMERIC(18,6),
    total_premium_value NUMERIC(18,6),
    strike_1            NUMERIC(18,6),
    strike_2            NUMERIC(18,6),
    trigger_2           NUMERIC(18,6),
    id_ccy              BIGINT,
    days_remaining      INTEGER,
    as_of_ts            TIMESTAMPTZ,

    row_hash            TEXT        NOT NULL,
    raw_payload_json    JSONB,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_exp_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_exp_row_snapshot FOREIGN KEY (id_org, id_exp_snapshot)
        REFERENCES expiries_snapshots(id_org, id_exp_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_exp_row_ac FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),
    CONSTRAINT fk_exp_row_ctpy FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),
    CONSTRAINT fk_exp_row_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_exp_snapshot, row_hash)

);
CREATE INDEX IF NOT EXISTS idx_expiries_org ON expiries(id_org);
CREATE INDEX IF NOT EXISTS idx_expiries_snapshot ON expiries(id_org, id_exp_snapshot);


-- ============================================================
-- NAV ESTIMATED
-- ============================================================

CREATE TABLE IF NOT EXISTS nav_estimated_snapshots (

    id_nav_est_snapshot    BIGSERIAL   PRIMARY KEY,
    uuid                   UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                 BIGINT      NOT NULL,

    id_run                 BIGINT      NOT NULL,
    id_f                   BIGINT      NOT NULL,

    as_of_ts               TIMESTAMPTZ NOT NULL,
    source_name            TEXT        NOT NULL DEFAULT 'file',
    source_file_name       TEXT,
    source_generated_at    TIMESTAMPTZ,
    loaded_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                 TEXT        NOT NULL DEFAULT 'loaded'
                           CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count              INTEGER     NOT NULL DEFAULT 0,
    is_official            BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                  TEXT,

    CONSTRAINT fk_nav_est_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_nav_est_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_nav_est_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)

);

CREATE INDEX IF NOT EXISTS idx_nav_estimated_snapshots_org ON nav_estimated_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_snapshots_fund ON nav_estimated_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_snapshots_as_of ON nav_estimated_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS nav_estimated (

    id_nav_est_row                BIGSERIAL   PRIMARY KEY,
    uuid                          UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                        BIGINT      NOT NULL,

    id_nav_est_snapshot           BIGINT      NOT NULL,
    id_f                          BIGINT      NOT NULL,

    nav_estimate                  NUMERIC(18,6),
    nav_estimate_weighted_by_time NUMERIC(18,6),
    comment                       TEXT,
    as_of_ts                      TIMESTAMPTZ,

    raw_payload_json              JSONB,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_nav_est_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_nav_est_row_snapshot FOREIGN KEY (id_org, id_nav_est_snapshot)
        REFERENCES nav_estimated_snapshots(id_org, id_nav_est_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_nav_est_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid)
);

CREATE INDEX IF NOT EXISTS idx_nav_estimated_org ON nav_estimated(id_org);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_snapshot ON nav_estimated(id_org, id_nav_est_snapshot);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_fund ON nav_estimated(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_as_of ON nav_estimated(id_org, as_of_ts);


-- ============================================================
-- LEVERAGES
-- ============================================================

CREATE TABLE IF NOT EXISTS leverages_snapshots (

    id_leverage_snapshot    BIGSERIAL   PRIMARY KEY,
    uuid                    UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                  BIGINT      NOT NULL,

    id_run                  BIGINT      NOT NULL,
    id_f                    BIGINT      NOT NULL,

    as_of_ts                TIMESTAMPTZ NOT NULL,
    source_name             TEXT        NOT NULL DEFAULT 'file',
    source_file_name        TEXT,
    source_generated_at     TIMESTAMPTZ,
    loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                  TEXT        NOT NULL DEFAULT 'loaded'
                            CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count               INTEGER     NOT NULL DEFAULT 0,
    is_official             BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                   TEXT,

    CONSTRAINT fk_leverage_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverage_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leverage_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)
);

CREATE INDEX IF NOT EXISTS idx_leverages_snapshots_org ON leverages_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_snapshots_fund ON leverages_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_snapshots_as_of ON leverages_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS leverages (

    id_leverage_row          BIGSERIAL   PRIMARY KEY,
    uuid                     UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                   BIGINT      NOT NULL,

    id_leverage_snapshot     BIGINT      NOT NULL,
    id_f                     BIGINT      NOT NULL,

    as_of_ts                 TIMESTAMPTZ,
    gross_leverage           NUMERIC(18,6),
    commitment_leverage      NUMERIC(18,6),

    raw_payload_json         JSONB,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leverage_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverage_row_snapshot FOREIGN KEY (id_org, id_leverage_snapshot)
        REFERENCES leverages_snapshots(id_org, id_leverage_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_leverage_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid)
);

CREATE INDEX IF NOT EXISTS idx_leverages_org ON leverages(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_snapshot ON leverages(id_org, id_leverage_snapshot);
CREATE INDEX IF NOT EXISTS idx_leverages_fund ON leverages(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_as_of ON leverages(id_org, as_of_ts);


-- ============================================================
-- LEVERAGES PER TRADE
-- ============================================================

CREATE TABLE IF NOT EXISTS leverages_per_trade_snapshots (

    id_leverage_trade_snapshot BIGSERIAL   PRIMARY KEY,
    uuid                       UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                     BIGINT      NOT NULL,

    id_run                     BIGINT      NOT NULL,
    id_f                       BIGINT      NOT NULL,

    as_of_ts                   TIMESTAMPTZ NOT NULL,
    source_name                TEXT        NOT NULL DEFAULT 'file',
    source_file_name           TEXT,
    source_generated_at        TIMESTAMPTZ,
    loaded_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                     TEXT        NOT NULL DEFAULT 'loaded'
                               CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count                  INTEGER     NOT NULL DEFAULT 0,
    is_official                BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                      TEXT,

    CONSTRAINT fk_leverages_trade_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverages_trade_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leverage_trade_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)
);

CREATE INDEX IF NOT EXISTS idx_leverages_trade_snapshots_org ON leverages_per_trade_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_snapshots_fund ON leverages_per_trade_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_snapshots_as_of ON leverages_per_trade_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS leverages_per_trade (

    id_leverage_trade_row      BIGSERIAL   PRIMARY KEY,
    uuid                       UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                     BIGINT      NOT NULL,

    id_leverage_trade_snapshot BIGINT      NOT NULL,
    id_f                       BIGINT      NOT NULL,

    as_of_ts                   TIMESTAMPTZ,
    trade_id                   BIGINT,
    id_ac                      BIGINT,
    trade_type                 TEXT,
    underlying_asset           TEXT,
    termination_date           DATE,
    buy_sell                   TEXT,
    notional                   NUMERIC(18,6),
    call_put                   TEXT,
    strike                     NUMERIC(18,6),
    trigger_value              NUMERIC(18,6),
    reference_spot             NUMERIC(18,6),
    counterparty_raw           TEXT,
    id_ctpy                    BIGINT,
    gross_leverage             NUMERIC(18,6),
    exposure_pct_nav           NUMERIC(18,6),
    compliance                 TEXT,

    raw_payload_json           JSONB,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leverages_trade_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverages_trade_row_snapshot FOREIGN KEY (id_org, id_leverage_trade_snapshot)
        REFERENCES leverages_per_trade_snapshots(id_org, id_leverage_trade_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_leverages_trade_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_leverages_trade_row_ac FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),
    CONSTRAINT fk_leverages_trade_row_ctpy FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leverage_trade_snapshot, trade_id)
);

CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_org ON leverages_per_trade(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_snapshot ON leverages_per_trade(id_org, id_leverage_trade_snapshot);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_fund ON leverages_per_trade(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_ac ON leverages_per_trade(id_ac);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_ctpy ON leverages_per_trade(id_org, id_ctpy);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_trade_id ON leverages_per_trade(id_org, trade_id);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_rows_as_of ON leverages_per_trade(id_org, as_of_ts);


-- ============================================================
-- LEVERAGES PER UNDERLYING
-- ============================================================

CREATE TABLE IF NOT EXISTS leverages_per_underlying_snapshots (

    id_leverage_underlying_snapshot BIGSERIAL   PRIMARY KEY,
    uuid                            UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                          BIGINT      NOT NULL,

    id_run                          BIGINT      NOT NULL,
    id_f                            BIGINT      NOT NULL,

    as_of_ts                        TIMESTAMPTZ NOT NULL,
    source_name                     TEXT        NOT NULL DEFAULT 'file',
    source_file_name                TEXT,
    source_generated_at             TIMESTAMPTZ,
    loaded_at                       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                          TEXT        NOT NULL DEFAULT 'loaded'
                                    CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count                       INTEGER     NOT NULL DEFAULT 0,
    is_official                     BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                           TEXT,

    CONSTRAINT fk_leverages_underlying_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverages_underlying_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_leverage_underlying_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)
);

CREATE INDEX IF NOT EXISTS idx_leverages_underlying_snapshots_org ON leverages_per_underlying_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_snapshots_fund ON leverages_per_underlying_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_snapshots_as_of ON leverages_per_underlying_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS leverages_per_underlying (

    id_leverage_underlying_row      BIGSERIAL   PRIMARY KEY,
    uuid                            UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                          BIGINT      NOT NULL,

    id_leverage_underlying_snapshot BIGINT      NOT NULL,
    id_f                            BIGINT      NOT NULL,

    as_of_ts                        TIMESTAMPTZ,
    id_ac                           BIGINT,
    underlying_asset                TEXT,
    gross_leverage                  NUMERIC(18,6),
    exposure_pct_nav                NUMERIC(18,6),
    compliance                      TEXT,
    exposure_pct_nav_final          NUMERIC(18,6),

    raw_payload_json                JSONB,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_leverages_underlying_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_leverages_underlying_row_snapshot FOREIGN KEY (id_org, id_leverage_underlying_snapshot)
        REFERENCES leverages_per_underlying_snapshots(id_org, id_leverage_underlying_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_leverages_underlying_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_leverages_underlying_row_ac FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),

    UNIQUE (uuid)
);

CREATE INDEX IF NOT EXISTS idx_leverages_underlying_rows_org ON leverages_per_underlying(id_org);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_rows_snapshot ON leverages_per_underlying(id_org, id_leverage_underlying_snapshot);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_rows_fund ON leverages_per_underlying(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_rows_ac ON leverages_per_underlying(id_ac);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_rows_as_of ON leverages_per_underlying(id_org, as_of_ts);


-- ============================================================
-- LONG SHORT DELTA
-- ============================================================

CREATE TABLE IF NOT EXISTS long_short_delta_snapshots (

    id_long_short_delta_snapshot BIGSERIAL   PRIMARY KEY,
    uuid                         UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                       BIGINT      NOT NULL,

    id_run                       BIGINT      NOT NULL,
    id_f                         BIGINT      NOT NULL,

    as_of_ts                     TIMESTAMPTZ NOT NULL,
    source_name                  TEXT        NOT NULL DEFAULT 'file',
    source_file_name             TEXT,
    source_generated_at          TIMESTAMPTZ,
    loaded_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                       TEXT        NOT NULL DEFAULT 'loaded'
                                 CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count                    INTEGER     NOT NULL DEFAULT 0,
    is_official                  BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                        TEXT,

    CONSTRAINT fk_long_short_delta_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_long_short_delta_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_long_short_delta_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)
);

CREATE INDEX IF NOT EXISTS idx_long_short_delta_snapshots_org ON long_short_delta_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_snapshots_fund ON long_short_delta_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_snapshots_as_of ON long_short_delta_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS long_short_delta (

    id_long_short_delta_row      BIGSERIAL   PRIMARY KEY,
    uuid                         UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                       BIGINT      NOT NULL,

    id_long_short_delta_snapshot BIGINT      NOT NULL,
    id_f                         BIGINT      NOT NULL,

    as_of_ts                     TIMESTAMPTZ NOT NULL,
    underlying_asset             TEXT        NOT NULL,
    long_delta_pct               NUMERIC(18,6),
    average_strike_long          NUMERIC(18,6),
    average_maturities_long      NUMERIC(18,6),
    short_delta_pct              NUMERIC(18,6),
    average_strike_short         NUMERIC(18,6),
    average_maturities_short     NUMERIC(18,6),
    net_delta_pct                NUMERIC(18,6),

    raw_payload_json             JSONB,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_long_short_delta_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_long_short_delta_row_snapshot FOREIGN KEY (id_org, id_long_short_delta_snapshot)
        REFERENCES long_short_delta_snapshots(id_org, id_long_short_delta_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_long_short_delta_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid)
);

CREATE INDEX IF NOT EXISTS idx_long_short_delta_rows_org ON long_short_delta(id_org);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_rows_snapshot ON long_short_delta(id_org, id_long_short_delta_snapshot);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_rows_fund ON long_short_delta(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_rows_as_of ON long_short_delta(id_org, as_of_ts);


-- ============================================================
-- COUNTERPARTY CONCENTRATION
-- ============================================================

CREATE TABLE IF NOT EXISTS counterparty_concentration_snapshots (

    id_ctpy_concentration_snapshot BIGSERIAL   PRIMARY KEY,
    uuid                           UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                         BIGINT      NOT NULL,

    id_run                         BIGINT      NOT NULL,
    id_f                           BIGINT      NOT NULL,

    as_of_ts                       TIMESTAMPTZ NOT NULL,
    source_name                    TEXT        NOT NULL DEFAULT 'file',
    source_file_name               TEXT,
    source_generated_at            TIMESTAMPTZ,
    loaded_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status                         TEXT        NOT NULL DEFAULT 'loaded'
                                   CHECK (status IN ('loaded','validated','official','replaced','failed')),
    row_count                      INTEGER     NOT NULL DEFAULT 0,
    is_official                    BOOLEAN     NOT NULL DEFAULT FALSE,
    notes                          TEXT,

    CONSTRAINT fk_ctpy_concentration_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_ctpy_concentration_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_ctpy_concentration_snapshot),
    UNIQUE (id_org, id_f, as_of_ts)
);

CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_snapshots_org ON counterparty_concentration_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_snapshots_fund ON counterparty_concentration_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_snapshots_as_of ON counterparty_concentration_snapshots(id_org, as_of_ts);


CREATE TABLE IF NOT EXISTS counterparty_concentration (

    id_ctpy_concentration_row      BIGSERIAL   PRIMARY KEY,
    uuid                           UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org                         BIGINT      NOT NULL,

    id_ctpy_concentration_snapshot BIGINT      NOT NULL,
    id_f                           BIGINT      NOT NULL,

    id_ctpy                        BIGINT      NOT NULL,
    as_of_ts                       TIMESTAMPTZ NOT NULL,
    
    mv_value                       NUMERIC(18,6),
    mv_nav_pct                     NUMERIC(18,6),
    compliance                     TEXT,

    raw_payload_json               JSONB,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ctpy_concentration_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_ctpy_concentration_row_snapshot FOREIGN KEY (id_org, id_ctpy_concentration_snapshot)
        REFERENCES counterparty_concentration_snapshots(id_org, id_ctpy_concentration_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_ctpy_concentration_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_ctpy_concentration_row_ctpy FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),

    UNIQUE (uuid)
);

CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_rows_org ON counterparty_concentration(id_org);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_rows_snapshot ON counterparty_concentration(id_org, id_ctpy_concentration_snapshot);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_rows_fund ON counterparty_concentration(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_rows_ctpy ON counterparty_concentration(id_org, id_ctpy);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_rows_as_of ON counterparty_concentration(id_org, as_of_ts);
