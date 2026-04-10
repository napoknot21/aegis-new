-- ============================================================
-- AEGIS - grouped ingestion runs for reporting snapshots
-- Purpose:
--   - create one parent run per logical snapshot batch
--   - attach all reporting snapshot families to that parent
--   - allow cascade deletion of a full intraday snapshot batch
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- INGESTION RUNS
-- ============================================================

CREATE TABLE IF NOT EXISTS ingestion_runs (

    id_ingestion_run BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_f             BIGINT      NOT NULL,
    id_run           BIGINT      NOT NULL,

    run_type         TEXT        NOT NULL DEFAULT 'reporting_snapshot'
                      CHECK (run_type IN ('reporting_snapshot','reporting_snapshot_partial','simm_only')),

    snapshot_ts      TIMESTAMPTZ NOT NULL,
    source_name      TEXT        NOT NULL DEFAULT 'mixed',
    started_at       TIMESTAMPTZ,
    loaded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status           TEXT        NOT NULL DEFAULT 'loaded'
                      CHECK (status IN ('loaded','validated','official','replaced','failed','partial')),

    notes            TEXT,

    CONSTRAINT fk_ingestion_run_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_ingestion_run_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_f, id_run)

);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_org ON ingestion_runs(id_org);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_fund ON ingestion_runs(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_run ON ingestion_runs(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_snapshot_ts ON ingestion_runs(id_org, id_f, snapshot_ts);


-- ============================================================
-- BACKFILL EXISTING SNAPSHOT HEADERS INTO INGESTION RUNS
-- ============================================================

WITH existing_runs AS (

    SELECT
        id_org,
        id_f,
        id_run,
        COALESCE(source_generated_at, loaded_at, as_of_date::TIMESTAMPTZ) AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'simm'::TEXT AS family_name
    FROM simm_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        snapshot_ts,
        'file'::TEXT AS source_name,
        imported_at AS loaded_at,
        CASE
            WHEN status = 'official_latest' THEN 'official'
            ELSE status
        END AS status,
        notes,
        'expiries'::TEXT AS family_name
    FROM expiries_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'nav_estimated'::TEXT AS family_name
    FROM nav_estimated_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'leverages'::TEXT AS family_name
    FROM leverages_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'leverages_per_trade'::TEXT AS family_name
    FROM leverages_per_trade_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'leverages_per_underlying'::TEXT AS family_name
    FROM leverages_per_underlying_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'long_short_delta'::TEXT AS family_name
    FROM long_short_delta_snapshots

    UNION ALL

    SELECT
        id_org,
        id_f,
        id_run,
        as_of_ts AS snapshot_ts,
        source_name,
        loaded_at,
        status,
        notes,
        'counterparty_concentration'::TEXT AS family_name
    FROM counterparty_concentration_snapshots

)
INSERT INTO ingestion_runs (
    id_org,
    id_f,
    id_run,
    run_type,
    snapshot_ts,
    source_name,
    started_at,
    loaded_at,
    status,
    notes
)
SELECT
    id_org,
    id_f,
    id_run,
    CASE
        WHEN COUNT(DISTINCT family_name) = 1 AND BOOL_AND(family_name = 'simm') THEN 'simm_only'
        WHEN COUNT(DISTINCT family_name) = 7 AND BOOL_AND(family_name <> 'simm') THEN 'reporting_snapshot'
        ELSE 'reporting_snapshot_partial'
    END AS run_type,
    MAX(snapshot_ts) AS snapshot_ts,
    CASE
        WHEN COUNT(DISTINCT source_name) = 1 THEN MIN(source_name)
        ELSE 'mixed'
    END AS source_name,
    MIN(loaded_at) AS started_at,
    MAX(loaded_at) AS loaded_at,
    CASE
        WHEN BOOL_OR(status = 'failed') THEN 'failed'
        WHEN BOOL_OR(status = 'official') THEN 'official'
        WHEN BOOL_OR(status = 'validated') THEN 'validated'
        ELSE 'loaded'
    END AS status,
    STRING_AGG(DISTINCT notes, ' | ') FILTER (WHERE notes IS NOT NULL AND BTRIM(notes) <> '') AS notes
FROM existing_runs
GROUP BY id_org, id_f, id_run
ON CONFLICT (id_org, id_f, id_run) DO NOTHING;


-- ============================================================
-- RUN INDEXES ON SNAPSHOT HEADERS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_simm_snapshots_run ON simm_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_expiries_snapshots_run ON expiries_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_nav_estimated_snapshots_run ON nav_estimated_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_leverages_snapshots_run ON leverages_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_leverages_trade_snapshots_run ON leverages_per_trade_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_leverages_underlying_snapshots_run ON leverages_per_underlying_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_long_short_delta_snapshots_run ON long_short_delta_snapshots(id_org, id_f, id_run);
CREATE INDEX IF NOT EXISTS idx_ctpy_concentration_snapshots_run ON counterparty_concentration_snapshots(id_org, id_f, id_run);


-- ============================================================
-- SNAPSHOT HEADERS -> INGESTION RUNS
-- ============================================================

ALTER TABLE simm_snapshots
    ADD CONSTRAINT fk_simm_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE expiries_snapshots
    ADD CONSTRAINT fk_exp_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE nav_estimated_snapshots
    ADD CONSTRAINT fk_nav_est_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE leverages_snapshots
    ADD CONSTRAINT fk_leverage_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE leverages_per_trade_snapshots
    ADD CONSTRAINT fk_leverages_trade_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE leverages_per_underlying_snapshots
    ADD CONSTRAINT fk_leverages_underlying_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE long_short_delta_snapshots
    ADD CONSTRAINT fk_long_short_delta_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;

ALTER TABLE counterparty_concentration_snapshots
    ADD CONSTRAINT fk_ctpy_concentration_snapshot_run
    FOREIGN KEY (id_org, id_f, id_run)
    REFERENCES ingestion_runs(id_org, id_f, id_run)
    ON DELETE CASCADE;


-- ============================================================
-- SNAPSHOT ROWS -> SNAPSHOT HEADERS WITH CASCADE
-- ============================================================

ALTER TABLE simm_snapshot_rows
    DROP CONSTRAINT IF EXISTS fk_simm_row_snapshot;
ALTER TABLE simm_snapshot_rows
    ADD CONSTRAINT fk_simm_row_snapshot
    FOREIGN KEY (id_org, id_simm_snapshot)
    REFERENCES simm_snapshots(id_org, id_simm_snapshot)
    ON DELETE CASCADE;

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_row_snapshot;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_row_snapshot
    FOREIGN KEY (id_org, id_exp_snapshot)
    REFERENCES expiries_snapshots(id_org, id_exp_snapshot)
    ON DELETE CASCADE;

ALTER TABLE nav_estimated
    DROP CONSTRAINT IF EXISTS fk_nav_est_row_snapshot;
ALTER TABLE nav_estimated
    ADD CONSTRAINT fk_nav_est_row_snapshot
    FOREIGN KEY (id_org, id_nav_est_snapshot)
    REFERENCES nav_estimated_snapshots(id_org, id_nav_est_snapshot)
    ON DELETE CASCADE;

ALTER TABLE leverages
    DROP CONSTRAINT IF EXISTS fk_leverage_row_snapshot;
ALTER TABLE leverages
    ADD CONSTRAINT fk_leverage_row_snapshot
    FOREIGN KEY (id_org, id_leverage_snapshot)
    REFERENCES leverages_snapshots(id_org, id_leverage_snapshot)
    ON DELETE CASCADE;

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_leverages_trade_row_snapshot;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_leverages_trade_row_snapshot
    FOREIGN KEY (id_org, id_leverage_trade_snapshot)
    REFERENCES leverages_per_trade_snapshots(id_org, id_leverage_trade_snapshot)
    ON DELETE CASCADE;

ALTER TABLE leverages_per_underlying
    DROP CONSTRAINT IF EXISTS fk_leverages_underlying_row_snapshot;
ALTER TABLE leverages_per_underlying
    ADD CONSTRAINT fk_leverages_underlying_row_snapshot
    FOREIGN KEY (id_org, id_leverage_underlying_snapshot)
    REFERENCES leverages_per_underlying_snapshots(id_org, id_leverage_underlying_snapshot)
    ON DELETE CASCADE;

ALTER TABLE long_short_delta
    DROP CONSTRAINT IF EXISTS fk_long_short_delta_row_snapshot;
ALTER TABLE long_short_delta
    ADD CONSTRAINT fk_long_short_delta_row_snapshot
    FOREIGN KEY (id_org, id_long_short_delta_snapshot)
    REFERENCES long_short_delta_snapshots(id_org, id_long_short_delta_snapshot)
    ON DELETE CASCADE;

ALTER TABLE counterparty_concentration
    DROP CONSTRAINT IF EXISTS fk_ctpy_concentration_row_snapshot;
ALTER TABLE counterparty_concentration
    ADD CONSTRAINT fk_ctpy_concentration_row_snapshot
    FOREIGN KEY (id_org, id_ctpy_concentration_snapshot)
    REFERENCES counterparty_concentration_snapshots(id_org, id_ctpy_concentration_snapshot)
    ON DELETE CASCADE;
