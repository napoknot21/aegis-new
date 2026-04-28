-- ============================================================
-- AEGIS - ingestion pipeline and trade reporting links
-- Purpose:
--   - add ingestion source/payload metadata
--   - add trade leg diff audit trail
--   - link expiry and leverage reporting rows back to trade referential
--   - add discretionary trade timestamps
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- INGESTION SOURCE CATALOGUE
-- ============================================================

CREATE TABLE IF NOT EXISTS ingestion_sources (

    id_source   BIGSERIAL   PRIMARY KEY,
    uuid        UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org      BIGINT      NOT NULL,

    code        TEXT        NOT NULL,
    name        TEXT        NOT NULL,
    description TEXT,

    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_source_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_source),
    UNIQUE (id_org, code)

);

CREATE INDEX IF NOT EXISTS idx_ingestion_sources_org ON ingestion_sources(id_org);
CREATE INDEX IF NOT EXISTS idx_ingestion_sources_org_active ON ingestion_sources(id_org, is_active);

COMMENT ON TABLE ingestion_sources IS
    'Tenant-scoped ingestion method catalogue. Examples: ICE Excel multi-file, ICE LibAPI, ICE Excel mono-file.';

INSERT INTO ingestion_sources (
    id_org,
    code,
    name,
    description
)
SELECT
    org.id_org,
    seed.code,
    seed.name,
    seed.description
FROM organisations AS org
CROSS JOIN (
    VALUES
        (
            'ice_excel_multi',
            'ICE Excel multi-file',
            'Three timestamped xlsx files: Trade Legs, Trades, and Underlying Totals.'
        ),
        (
            'ice_libapi',
            'ICE LibAPI',
            'HTTP API calls per book. Returns JSON and does not require physical files.'
        ),
        (
            'ice_excel_mono',
            'ICE Excel mono-file',
            'Single combined xlsx file intended to replace multi-file and LibAPI ingestion.'
        )
) AS seed(code, name, description)
ON CONFLICT (id_org, code)
DO NOTHING;


-- ============================================================
-- INGESTION RUN SOURCE LINK
-- ============================================================

ALTER TABLE ingestion_runs
    ADD COLUMN IF NOT EXISTS id_source BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'ingestion_runs'::regclass
          AND conname = 'uq_ingestion_runs_org_fund_ingestion_run'
    ) THEN
        ALTER TABLE ingestion_runs
            ADD CONSTRAINT uq_ingestion_runs_org_fund_ingestion_run
            UNIQUE (id_org, id_f, id_ingestion_run);
    END IF;
END $$;

ALTER TABLE ingestion_runs
    DROP CONSTRAINT IF EXISTS fk_ingestion_run_source;
ALTER TABLE ingestion_runs
    ADD CONSTRAINT fk_ingestion_run_source
    FOREIGN KEY (id_org, id_source)
    REFERENCES ingestion_sources(id_org, id_source);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_source
    ON ingestion_runs(id_org, id_source);

COMMENT ON COLUMN ingestion_runs.id_source IS
    'Optional ingestion source used to produce this run. Nullable for historical runs.';


-- ============================================================
-- RAW INGESTION PAYLOADS
-- ============================================================

CREATE TABLE IF NOT EXISTS raw_ingestion_payloads (

    id_payload       BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_f             BIGINT      NOT NULL,
    id_source        BIGINT      NOT NULL,
    id_ingestion_run BIGINT,

    payload_type     TEXT        NOT NULL
                     CHECK (payload_type IN ('file', 'api_response')),

    file_role        TEXT
                     CHECK (file_role IS NULL OR file_role IN (
                         'trade_legs',
                         'trades',
                         'underlying_totals',
                         'combined'
                     )),
    file_name        TEXT,
    storage_path     TEXT,
    file_checksum    TEXT,

    api_endpoint     TEXT,
    api_params       JSONB,
    raw_json         JSONB,

    source_ts        TIMESTAMPTZ,
    received_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    row_count_raw    INTEGER,
    notes            TEXT,

    CONSTRAINT fk_payload_org FOREIGN KEY (id_org)
        REFERENCES organisations(id_org),
    CONSTRAINT fk_payload_fund FOREIGN KEY (id_org, id_f)
        REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_payload_source FOREIGN KEY (id_org, id_source)
        REFERENCES ingestion_sources(id_org, id_source),
    CONSTRAINT fk_payload_run FOREIGN KEY (id_org, id_f, id_ingestion_run)
        REFERENCES ingestion_runs(id_org, id_f, id_ingestion_run)
        ON DELETE SET NULL (id_ingestion_run),

    UNIQUE (uuid),
    UNIQUE (id_org, id_f, file_checksum)

);

CREATE INDEX IF NOT EXISTS idx_raw_payloads_org ON raw_ingestion_payloads(id_org);
CREATE INDEX IF NOT EXISTS idx_raw_payloads_run ON raw_ingestion_payloads(id_org, id_f, id_ingestion_run);
CREATE INDEX IF NOT EXISTS idx_raw_payloads_source ON raw_ingestion_payloads(id_org, id_source);
CREATE INDEX IF NOT EXISTS idx_raw_payloads_file_checksum
    ON raw_ingestion_payloads(id_org, id_f, file_checksum)
    WHERE file_checksum IS NOT NULL;

COMMENT ON TABLE raw_ingestion_payloads IS
    'Raw ingestion payload metadata. A payload can be an Excel file or an API response.';


-- ============================================================
-- INGESTION FIELD MAPPINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS ingestion_field_mappings (

    id_mapping     BIGSERIAL PRIMARY KEY,
    uuid           UUID      NOT NULL DEFAULT uuid_generate_v4(),

    id_org         BIGINT    NOT NULL,
    id_source      BIGINT    NOT NULL,

    target_table   TEXT      NOT NULL,
    target_column  TEXT      NOT NULL,
    source_field   TEXT      NOT NULL,

    transform_type TEXT      NOT NULL
                  CHECK (transform_type IN ('direct', 'lookup', 'computed', 'constant')),

    lookup_table   TEXT,
    lookup_column  TEXT,

    cast_hint      TEXT,
    constant_value TEXT,

    is_required    BOOLEAN   NOT NULL DEFAULT FALSE,
    is_active      BOOLEAN   NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_mapping_org FOREIGN KEY (id_org)
        REFERENCES organisations(id_org),
    CONSTRAINT fk_mapping_source FOREIGN KEY (id_org, id_source)
        REFERENCES ingestion_sources(id_org, id_source),

    UNIQUE (uuid),
    UNIQUE (id_org, id_source, target_table, target_column)

);

CREATE INDEX IF NOT EXISTS idx_field_mappings_source
    ON ingestion_field_mappings(id_org, id_source);
CREATE INDEX IF NOT EXISTS idx_field_mappings_target
    ON ingestion_field_mappings(id_org, target_table, target_column);

COMMENT ON TABLE ingestion_field_mappings IS
    'Tenant/source-specific mapping from raw source fields to target database columns.';


-- ============================================================
-- TRADE LEG LIFECYCLE COLUMNS
-- ============================================================

ALTER TABLE trade_disc_legs
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;

ALTER TABLE trade_disc_legs
    ALTER COLUMN status SET DEFAULT 'active',
    ALTER COLUMN first_seen_at SET DEFAULT NOW(),
    ALTER COLUMN last_seen_at SET DEFAULT NOW();

UPDATE trade_disc_legs
SET
    status = COALESCE(status, 'active'),
    first_seen_at = COALESCE(first_seen_at, NOW()),
    last_seen_at = COALESCE(last_seen_at, NOW())
WHERE status IS NULL
   OR first_seen_at IS NULL
   OR last_seen_at IS NULL;

ALTER TABLE trade_disc_legs
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN first_seen_at SET NOT NULL,
    ALTER COLUMN last_seen_at SET NOT NULL;

ALTER TABLE trade_disc_legs
    DROP CONSTRAINT IF EXISTS trade_disc_legs_status_check;
ALTER TABLE trade_disc_legs
    ADD CONSTRAINT trade_disc_legs_status_check
    CHECK (status IN ('active', 'expired', 'terminated', 'cancelled', 'disappeared'));

CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_status
    ON trade_disc_legs(id_org, status);
CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_last_seen
    ON trade_disc_legs(id_org, last_seen_at);

CREATE OR REPLACE FUNCTION set_trade_disc_leg_status_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        NEW.status_updated_at = NOW();
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_trade_disc_legs_status_updated_at ON trade_disc_legs;
CREATE TRIGGER trg_trade_disc_legs_status_updated_at
BEFORE UPDATE OF status ON trade_disc_legs
FOR EACH ROW
EXECUTE FUNCTION set_trade_disc_leg_status_updated_at();


-- ============================================================
-- TRADE LEG DIFF AUDIT TRAIL
-- ============================================================

CREATE TABLE IF NOT EXISTS trade_leg_diffs (

    id_diff          BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_f             BIGINT      NOT NULL,
    id_ingestion_run BIGINT      NOT NULL,
    id_leg           BIGINT,

    ice_leg_id       TEXT        NOT NULL,

    diff_type        TEXT        NOT NULL
                     CHECK (diff_type IN ('new', 'modified', 'unchanged', 'disappeared')),

    changed_columns  TEXT[],
    snapshot_before  JSONB,
    snapshot_after   JSONB,
    detected_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_diff_org FOREIGN KEY (id_org)
        REFERENCES organisations(id_org),
    CONSTRAINT fk_diff_fund FOREIGN KEY (id_org, id_f)
        REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_diff_run FOREIGN KEY (id_org, id_f, id_ingestion_run)
        REFERENCES ingestion_runs(id_org, id_f, id_ingestion_run)
        ON DELETE CASCADE,
    CONSTRAINT fk_diff_leg FOREIGN KEY (id_org, id_leg)
        REFERENCES trade_disc_legs(id_org, id_leg),

    UNIQUE (uuid)

);

CREATE INDEX IF NOT EXISTS idx_leg_diffs_run
    ON trade_leg_diffs(id_org, id_f, id_ingestion_run);
CREATE INDEX IF NOT EXISTS idx_leg_diffs_leg
    ON trade_leg_diffs(id_org, id_leg);
CREATE INDEX IF NOT EXISTS idx_leg_diffs_type
    ON trade_leg_diffs(id_org, diff_type);
CREATE INDEX IF NOT EXISTS idx_leg_diffs_ice_leg
    ON trade_leg_diffs(id_org, ice_leg_id);

COMMENT ON TABLE trade_leg_diffs IS
    'Per-ingestion audit trail of new, modified, unchanged, and disappeared trade legs.';


-- ============================================================
-- REPORTING ROWS -> TRADE REFERENTIAL
-- ============================================================

ALTER TABLE expiries
    ADD COLUMN IF NOT EXISTS id_spe BIGINT,
    ADD COLUMN IF NOT EXISTS id_leg BIGINT,
    ADD COLUMN IF NOT EXISTS ice_trade_id TEXT,
    ADD COLUMN IF NOT EXISTS ice_leg_id TEXT;

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_spe;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_spe
    FOREIGN KEY (id_org, id_spe)
    REFERENCES trade_spe(id_org, id_spe);

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_leg;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_leg
    FOREIGN KEY (id_org, id_leg)
    REFERENCES trade_disc_legs(id_org, id_leg);

CREATE INDEX IF NOT EXISTS idx_expiries_spe
    ON expiries(id_org, id_spe)
    WHERE id_spe IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_expiries_leg
    ON expiries(id_org, id_leg)
    WHERE id_leg IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_expiries_ice_trade_id
    ON expiries(id_org, ice_trade_id)
    WHERE ice_trade_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_expiries_ice_leg_id
    ON expiries(id_org, ice_leg_id)
    WHERE ice_leg_id IS NOT NULL;

ALTER TABLE leverages_per_trade
    ADD COLUMN IF NOT EXISTS id_spe BIGINT,
    ADD COLUMN IF NOT EXISTS id_leg BIGINT,
    ADD COLUMN IF NOT EXISTS ice_leg_id TEXT,
    ADD COLUMN IF NOT EXISTS ice_trade_id TEXT;

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_lev_trade_spe;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_lev_trade_spe
    FOREIGN KEY (id_org, id_spe)
    REFERENCES trade_spe(id_org, id_spe);

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_lev_trade_leg;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_lev_trade_leg
    FOREIGN KEY (id_org, id_leg)
    REFERENCES trade_disc_legs(id_org, id_leg);

CREATE INDEX IF NOT EXISTS idx_lev_trade_spe
    ON leverages_per_trade(id_org, id_spe)
    WHERE id_spe IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lev_trade_leg
    ON leverages_per_trade(id_org, id_leg)
    WHERE id_leg IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lev_trade_ice_id
    ON leverages_per_trade(id_org, ice_trade_id)
    WHERE ice_trade_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lev_trade_ice_leg_id
    ON leverages_per_trade(id_org, ice_leg_id)
    WHERE ice_leg_id IS NOT NULL;


-- ============================================================
-- DISCRETIONARY TRADE HIERARCHY AND LOOKUP INDEXES
-- ============================================================

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_spe;

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_trade;
ALTER TABLE trade_disc
    ADD CONSTRAINT fk_disc_trade
    FOREIGN KEY (id_org, id_spe)
    REFERENCES trades(id_org, id_spe);

CREATE UNIQUE INDEX IF NOT EXISTS uq_trade_disc_ice_trade_id
    ON trade_disc(id_org, ice_trade_id)
    WHERE ice_trade_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_leg_id
    ON trade_disc_legs(id_org, leg_id);


-- ============================================================
-- DISCRETIONARY TRADE TIMESTAMPS
-- ============================================================

ALTER TABLE trade_disc
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

ALTER TABLE trade_disc
    ALTER COLUMN created_at SET DEFAULT NOW(),
    ALTER COLUMN updated_at SET DEFAULT NOW();

UPDATE trade_disc
SET
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, NOW())
WHERE created_at IS NULL
   OR updated_at IS NULL;

ALTER TABLE trade_disc
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

DROP TRIGGER IF EXISTS trg_trade_disc_set_updated_at ON trade_disc;
CREATE TRIGGER trg_trade_disc_set_updated_at
BEFORE UPDATE ON trade_disc
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();


-- ============================================================
-- LOCKDOWN CONSISTENCY FOR OBJECTS CREATED AFTER SECURITY MIGRATION
-- ============================================================

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;
