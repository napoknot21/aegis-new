BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(10);

INSERT INTO currencies (
    id_ccy,
    code,
    name,
    symbol,
    iso_numeric,
    decimals,
    sort_order,
    is_active
)
VALUES
    (910001, 'TS1', 'Test Snapshot Currency', 'TS1', 901, 2, 901, TRUE);

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (910001, 'TESTORG_SNAP', 'Test Org Snapshot', 'Test Org Snapshot');

INSERT INTO funds (
    id_f,
    id_org,
    id_ccy,
    name,
    code
)
VALUES
    (910001, 910001, 910001, 'Snapshot Fund', 'SNAPFUND');

WITH inserted_run AS (
    INSERT INTO ingestion_runs (
        id_org,
        id_f,
        snapshot_ts,
        source_name,
        status,
        notes
    )
    VALUES (
        910001,
        910001,
        TIMESTAMPTZ '2026-04-14 10:00:00+00',
        'test_loader',
        'loaded',
        'pgtap reporting snapshot batch'
    )
    RETURNING id_run
)
SELECT ok(
    (SELECT id_run > 0 FROM inserted_run),
    'ingestion_runs auto-generates id_run'
);

INSERT INTO simm_snapshots (
    id_org,
    id_run,
    id_f,
    as_of_date,
    source_name,
    status,
    row_count,
    is_official,
    notes
)
VALUES (
    910001,
    42,
    910001,
    DATE '2026-04-14',
    'libapi',
    'official',
    1,
    TRUE,
    'daily simm snapshot'
);

INSERT INTO simm_snapshot_rows (
    id_org,
    id_simm_snapshot,
    id_f,
    as_of_date,
    counterparty_raw,
    im_value
)
SELECT
    910001,
    id_simm_snapshot,
    910001,
    DATE '2026-04-14',
    'CP-SIMM-1',
    10.25
FROM simm_snapshots
WHERE id_org = 910001;

WITH run_ref AS (
    SELECT id_run
    FROM ingestion_runs
    WHERE id_org = 910001
      AND id_f = 910001
),
exp_snapshot AS (
    INSERT INTO expiries_snapshots (
        id_org,
        id_run,
        id_f,
        snapshot_date,
        snapshot_ts,
        file_name,
        status,
        row_count,
        is_latest_for_day,
        notes
    )
    SELECT
        910001,
        id_run,
        910001,
        DATE '2026-04-14',
        TIMESTAMPTZ '2026-04-14 10:00:00+00',
        'expiries.csv',
        'official',
        1,
        TRUE,
        'expiries slice'
    FROM run_ref
    RETURNING id_exp_snapshot
)
INSERT INTO expiries (
    id_org,
    id_exp_snapshot,
    row_hash,
    as_of_ts
)
SELECT
    910001,
    id_exp_snapshot,
    'exp-row-1',
    TIMESTAMPTZ '2026-04-14 10:00:00+00'
FROM exp_snapshot;

WITH run_ref AS (
    SELECT id_run
    FROM ingestion_runs
    WHERE id_org = 910001
      AND id_f = 910001
),
nav_snapshot AS (
    INSERT INTO nav_estimated_snapshots (
        id_org,
        id_run,
        id_f,
        as_of_ts,
        source_name,
        status,
        row_count,
        is_official,
        notes
    )
    SELECT
        910001,
        id_run,
        910001,
        TIMESTAMPTZ '2026-04-14 10:00:00+00',
        'file',
        'official',
        1,
        TRUE,
        'nav slice'
    FROM run_ref
    RETURNING id_nav_est_snapshot
)
INSERT INTO nav_estimated (
    id_org,
    id_nav_est_snapshot,
    id_f,
    nav_estimate,
    as_of_ts
)
SELECT
    910001,
    id_nav_est_snapshot,
    910001,
    123.45,
    TIMESTAMPTZ '2026-04-14 10:00:00+00'
FROM nav_snapshot;

SELECT is(
    (
        WITH combined AS (
            SELECT id_run
            FROM expiries_snapshots
            WHERE id_org = 910001
            UNION ALL
            SELECT id_run
            FROM nav_estimated_snapshots
            WHERE id_org = 910001
        )
        SELECT COUNT(DISTINCT id_run)::INT
        FROM combined
    ),
    1,
    'intraday snapshot families share one parent id_run'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM ingestion_runs WHERE id_org = 910001 AND id_f = 910001),
    1,
    'one parent ingestion run exists for the batch'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM expiries WHERE id_org = 910001),
    1,
    'expiries row is present before deleting the parent batch'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM nav_estimated WHERE id_org = 910001),
    1,
    'nav row is present before deleting the parent batch'
);

DELETE FROM ingestion_runs
WHERE id_org = 910001
  AND id_f = 910001;

SELECT is(
    (SELECT COUNT(*)::INT FROM expiries_snapshots WHERE id_org = 910001),
    0,
    'deleting the parent batch removes expiries snapshot headers'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM expiries WHERE id_org = 910001),
    0,
    'deleting the parent batch removes expiries rows'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM nav_estimated WHERE id_org = 910001),
    0,
    'deleting the parent batch removes nav rows'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM simm_snapshots WHERE id_org = 910001),
    1,
    'deleting an intraday batch does not delete SIMM snapshots'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM simm_snapshot_rows WHERE id_org = 910001),
    1,
    'SIMM rows remain independent from intraday snapshot deletion'
);

SELECT * FROM finish();

ROLLBACK;
