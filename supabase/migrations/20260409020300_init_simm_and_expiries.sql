-- ============================================================
-- AEGIS - official migration: SIMM and expiries
-- Source draft: supabase/drafts/core-schema-draft.sql
--
-- Scope:
--   - simm_snapshots
--   - simm_snapshot_rows
--   - expiries_snapshots
--   - expiries
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
    CONSTRAINT fk_simm_row_snapshot FOREIGN KEY (id_org, id_simm_snapshot) REFERENCES simm_snapshots(id_org, id_simm_snapshot),
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
                        CHECK (status IN ('loaded','validated','official_latest','replaced','failed')),
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
    CONSTRAINT fk_exp_row_snapshot FOREIGN KEY (id_org, id_exp_snapshot) REFERENCES expiries_snapshots(id_org, id_exp_snapshot),
    CONSTRAINT fk_exp_row_ac FOREIGN KEY (id_ac) REFERENCES asset_classes(id_ac),
    CONSTRAINT fk_exp_row_ctpy FOREIGN KEY (id_org, id_ctpy) REFERENCES counterparties(id_org, id_ctpy),
    CONSTRAINT fk_exp_row_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_exp_snapshot, row_hash)

);
CREATE INDEX IF NOT EXISTS idx_expiries_org ON expiries(id_org);
CREATE INDEX IF NOT EXISTS idx_expiries_snapshot ON expiries(id_org, id_exp_snapshot);
