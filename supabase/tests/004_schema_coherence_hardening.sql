BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(8);

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
    (930001, 'TS3', 'Test Coherence Currency', 'TS3', 903, 2, 903, TRUE);

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (930001, 'TESTORG_COH', 'Test Org Coherence', 'Test Org Coherence');

INSERT INTO offices (
    id_off,
    id_org,
    code,
    name
)
VALUES
    (930001, 930001, 'LUX', 'Luxembourg'),
    (930002, 930001, 'LDN', 'London');

INSERT INTO users (
    id_user,
    id_org,
    entra_oid,
    email,
    display_name
)
VALUES
    (
        930001,
        930001,
        '22222222-2222-2222-2222-222222222222',
        'coherence-user@example.com',
        'Coherence User'
    );

INSERT INTO funds (
    id_f,
    id_org,
    id_ccy,
    name,
    code
)
VALUES
    (930001, 930001, 930001, 'Coherence Fund A', 'COHFUNDA'),
    (930002, 930001, 930001, 'Coherence Fund B', 'COHFUNDB');

INSERT INTO banks (
    id_bank,
    id_org,
    name,
    code
)
VALUES
    (930001, 930001, 'Coherence Bank', 'COHBANK');

INSERT INTO counterparties (
    id_ctpy,
    id_org,
    id_bank,
    ice_name,
    ext_code
)
VALUES
    (930001, 930001, 930001, 'Coherence Counterparty', 'COHCP');

INSERT INTO ingestion_runs (
    id_ingestion_run,
    id_org,
    id_f,
    id_run,
    run_type,
    snapshot_ts,
    source_name,
    status,
    notes
)
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        'reporting_snapshot',
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        'pgtap',
        'loaded',
        'schema coherence test run'
    );

INSERT INTO simm_snapshots (
    id_simm_snapshot,
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
VALUES
    (930001, 930001, 930101, 930001, DATE '2026-04-14', 'libapi', 'loaded', 0, FALSE, 'unofficial 1'),
    (930002, 930001, 930102, 930001, DATE '2026-04-14', 'libapi', 'validated', 0, FALSE, 'unofficial 2'),
    (930003, 930001, 930103, 930001, DATE '2026-04-14', 'libapi', 'official', 0, TRUE, 'official');

SELECT is(
    (
        SELECT COUNT(*)::INT
        FROM simm_snapshots
        WHERE id_org = 930001
          AND id_f = 930001
          AND as_of_date = DATE '2026-04-14'
          AND is_official = FALSE
    ),
    2,
    'multiple non-official SIMM snapshots can coexist for the same fund and day'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO simm_snapshots (
            id_simm_snapshot,
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
            930004,
            930001,
            930104,
            930001,
            DATE '2026-04-14',
            'libapi',
            'official',
            0,
            TRUE,
            'duplicate official'
        );
        RAISE EXCEPTION 'expected unique_violation for duplicate official simm snapshot';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('only one official SIMM snapshot is allowed per fund and day');

DO $$
BEGIN
    BEGIN
        INSERT INTO simm_snapshot_rows (
            id_simm_row,
            id_org,
            id_simm_snapshot,
            id_f,
            as_of_date,
            counterparty_raw,
            im_value
        )
        VALUES (
            930001,
            930001,
            930003,
            930002,
            DATE '2026-04-14',
            'CP-MISMATCH',
            12.50
        );
        RAISE EXCEPTION 'expected foreign_key_violation for mismatched simm row fund';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('SIMM rows must match the parent snapshot fund and date');

INSERT INTO user_offices (
    id_user_off,
    id_org,
    id_user,
    id_off,
    is_primary,
    is_active
)
VALUES
    (930001, 930001, 930001, 930001, TRUE, TRUE);

DO $$
BEGIN
    BEGIN
        INSERT INTO user_offices (
            id_user_off,
            id_org,
            id_user,
            id_off,
            is_primary,
            is_active
        )
        VALUES
            (930002, 930001, 930001, 930002, TRUE, TRUE);
        RAISE EXCEPTION 'expected unique_violation for duplicate primary user office';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('a user can only have one active primary office');

INSERT INTO fund_office_access (
    id,
    id_org,
    id_f,
    id_off,
    access_type,
    is_active
)
VALUES
    (930001, 930001, 930001, 930001, 'primary', TRUE);

DO $$
BEGIN
    BEGIN
        INSERT INTO fund_office_access (
            id,
            id_org,
            id_f,
            id_off,
            access_type,
            is_active
        )
        VALUES
            (930002, 930001, 930001, 930002, 'primary', TRUE);
        RAISE EXCEPTION 'expected unique_violation for duplicate primary fund office';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('a fund can only have one active primary office');

INSERT INTO nav_estimated_snapshots (
    id_nav_est_snapshot,
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
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        'file',
        'official',
        1,
        TRUE,
        'nav header'
    );

INSERT INTO nav_estimated (
    id_nav_est_row,
    id_org,
    id_nav_est_snapshot,
    id_f,
    nav_estimate,
    as_of_ts
)
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        101.25,
        TIMESTAMPTZ '2026-04-14 11:00:00+00'
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO nav_estimated (
            id_nav_est_row,
            id_org,
            id_nav_est_snapshot,
            id_f,
            nav_estimate,
            as_of_ts
        )
        VALUES
            (
                930002,
                930001,
                930001,
                930001,
                102.50,
                TIMESTAMPTZ '2026-04-14 11:00:00+00'
            );
        RAISE EXCEPTION 'expected unique_violation for duplicate nav row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('nav_estimated stays one-row-per-snapshot');

INSERT INTO long_short_delta_snapshots (
    id_long_short_delta_snapshot,
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
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        'file',
        'official',
        1,
        TRUE,
        'lsd header'
    );

INSERT INTO long_short_delta (
    id_long_short_delta_row,
    id_org,
    id_long_short_delta_snapshot,
    id_f,
    as_of_ts,
    underlying_asset,
    long_delta_pct
)
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        'SPX',
        0.15
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO long_short_delta (
            id_long_short_delta_row,
            id_org,
            id_long_short_delta_snapshot,
            id_f,
            as_of_ts,
            underlying_asset,
            long_delta_pct
        )
        VALUES
            (
                930002,
                930001,
                930001,
                930001,
                TIMESTAMPTZ '2026-04-14 11:00:00+00',
                'SPX',
                0.18
            );
        RAISE EXCEPTION 'expected unique_violation for duplicate long_short_delta row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('long_short_delta stays unique per snapshot and underlying');

INSERT INTO counterparty_concentration_snapshots (
    id_ctpy_concentration_snapshot,
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
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        'file',
        'official',
        1,
        TRUE,
        'ctpy header'
    );

INSERT INTO counterparty_concentration (
    id_ctpy_concentration_row,
    id_org,
    id_ctpy_concentration_snapshot,
    id_f,
    id_ctpy,
    as_of_ts,
    mv_value
)
VALUES
    (
        930001,
        930001,
        930001,
        930001,
        930001,
        TIMESTAMPTZ '2026-04-14 11:00:00+00',
        250.00
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO counterparty_concentration (
            id_ctpy_concentration_row,
            id_org,
            id_ctpy_concentration_snapshot,
            id_f,
            id_ctpy,
            as_of_ts,
            mv_value
        )
        VALUES
            (
                930002,
                930001,
                930001,
                930001,
                930001,
                TIMESTAMPTZ '2026-04-14 11:00:00+00',
                255.00
            );
        RAISE EXCEPTION 'expected unique_violation for duplicate counterparty concentration row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('counterparty_concentration stays unique per snapshot and counterparty');

SELECT * FROM finish();

ROLLBACK;
