BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(9);

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
    (950001, 'TFA', 'Test FK Currency A', 'TFA', 951, 2, 951, TRUE);

INSERT INTO asset_classes (
    id_ac,
    code,
    ice_code,
    name,
    description,
    sort_order,
    is_active
)
VALUES
    (950001, 'TFK', 'TFK', 'Test FK Asset Class', 'Test asset class for FK hardening', 951, TRUE);

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (950001, 'TESTORG_FK', 'Test Org FK', 'Test Org FK');

INSERT INTO funds (
    id_f,
    id_org,
    id_ccy,
    name,
    code
)
VALUES
    (950001, 950001, 950001, 'FK Fund A', 'FKFUNDA'),
    (950002, 950001, 950001, 'FK Fund B', 'FKFUNDB');

INSERT INTO books (
    id_book,
    id_org,
    name,
    id_f
)
VALUES
    (950001, 950001, 'FK Book A', 950001),
    (950002, 950001, 'FK Book B', 950002);

DO $$
BEGIN
    BEGIN
        INSERT INTO books (
            id_book,
            id_org,
            name,
            id_f,
            parent_id
        )
        VALUES
            (950099, 950001, 'Cross Fund Child Book', 950002, 950001);
        RAISE EXCEPTION 'expected foreign_key_violation for cross-fund book parent';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('books cannot use a parent from another fund');

INSERT INTO banks (
    id_bank,
    id_org,
    name,
    code
)
VALUES
    (950001, 950001, 'FK Bank', 'FKBANK');

INSERT INTO counterparties (
    id_ctpy,
    id_org,
    id_bank,
    ice_name,
    ext_code
)
VALUES
    (950001, 950001, 950001, 'FK Counterparty', 'FKCP');

INSERT INTO trade_types (
    id_type,
    id_org,
    name,
    code
)
VALUES
    (950001, 950001, 'FK Trade Type', 'FKT');

INSERT INTO trade_disc_labels (
    id_label,
    id_org,
    code
)
VALUES
    (950001, 950001, 'FKDISC');

INSERT INTO trade_spe (
    id_spe,
    id_org
)
VALUES
    (950001, 950001),
    (950002, 950001),
    (950003, 950001),
    (950004, 950001);

INSERT INTO trades (
    id_trade,
    id_org,
    id_spe,
    id_type,
    id_f,
    status
)
VALUES
    (950001, 950001, 950001, 950001, 950001, 'booked'),
    (950002, 950001, 950002, 950001, 950002, 'booked'),
    (950003, 950001, 950003, 950001, 950001, 'booked'),
    (950004, 950001, 950004, 950001, 950001, 'booked');

INSERT INTO trade_disc (
    id_spe,
    id_org,
    id_book,
    id_ctpy,
    id_label,
    ice_trade_id
)
VALUES
    (950001, 950001, 950001, 950001, 950001, 'FK-TRADE-A'),
    (950002, 950001, 950002, 950001, 950001, 'FK-TRADE-B');

SELECT is(
    (
        SELECT id_f
        FROM trade_disc
        WHERE id_org = 950001
          AND id_spe = 950001
    ),
    950001::BIGINT,
    'trade_disc inherits id_f from the parent trade'
);

INSERT INTO trade_disc_legs (
    id_leg,
    id_org,
    id_disc,
    id_ac,
    leg_id,
    direction,
    notional,
    id_ccy
)
VALUES
    (950001, 950001, 950001, 950001, 'FK-LEG-A', 'Buy', 100.00, 950001),
    (950002, 950001, 950002, 950001, 'FK-LEG-B', 'Sell', 50.00, 950001);

SELECT is(
    (
        SELECT id_f
        FROM trade_disc_legs
        WHERE id_org = 950001
          AND id_leg = 950001
    ),
    950001::BIGINT,
    'trade_disc_legs inherits id_f from the parent DISC trade'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO trade_disc (
            id_spe,
            id_org,
            id_book,
            id_ctpy,
            id_label,
            ice_trade_id
        )
        VALUES
            (950003, 950001, 950002, 950001, 950001, 'FK-TRADE-BAD-BOOK');
        RAISE EXCEPTION 'expected foreign_key_violation for trade_disc book fund mismatch';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('trade_disc book must belong to the same fund as the trade');

INSERT INTO books (
    id_book,
    id_org,
    name,
    id_f
)
VALUES
    (950003, 950001, 'FK Book A Other', 950001);

INSERT INTO trade_disc (
    id_spe,
    id_org,
    id_book,
    id_ctpy,
    id_label,
    ice_trade_id
)
VALUES
    (950004, 950001, 950003, 950001, 950001, 'FK-TRADE-A-OTHER');

INSERT INTO trade_disc_legs (
    id_leg,
    id_org,
    id_disc,
    id_ac,
    leg_id,
    direction,
    notional,
    id_ccy
)
VALUES
    (950004, 950001, 950004, 950001, 'FK-LEG-A-OTHER', 'Buy', 25.00, 950001);

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
        950001,
        950001,
        950001,
        950001,
        'reporting_snapshot',
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'pgtap',
        'loaded',
        'FK hardening fund A run'
    ),
    (
        950002,
        950001,
        950002,
        950002,
        'reporting_snapshot',
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'pgtap',
        'loaded',
        'FK hardening fund B run'
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO trade_leg_diffs (
            id_diff,
            id_org,
            id_f,
            id_ingestion_run,
            id_leg,
            ice_leg_id,
            diff_type
        )
        VALUES
            (950001, 950001, 950002, 950002, 950001, 'FK-LEG-A', 'modified');
        RAISE EXCEPTION 'expected foreign_key_violation for trade_leg_diffs leg fund mismatch';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('trade_leg_diffs id_f must match the linked leg fund');

INSERT INTO expiries_snapshots (
    id_exp_snapshot,
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
VALUES
    (
        950001,
        950001,
        950001,
        950001,
        DATE '2026-04-29',
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'fk-expiries.csv',
        'loaded',
        1,
        TRUE,
        'FK hardening expiries'
    );

INSERT INTO expiries (
    id_exp_row,
    id_org,
    id_exp_snapshot,
    id_spe,
    id_leg,
    row_hash,
    as_of_ts
)
VALUES
    (
        950001,
        950001,
        950001,
        950001,
        950001,
        'fk-expiry-ok',
        TIMESTAMPTZ '2026-04-29 10:00:00+00'
    );

SELECT is(
    (
        SELECT id_f
        FROM expiries
        WHERE id_org = 950001
          AND id_exp_row = 950001
    ),
    950001::BIGINT,
    'expiries inherits id_f from the parent snapshot'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO expiries (
            id_exp_row,
            id_org,
            id_exp_snapshot,
            id_spe,
            id_leg,
            row_hash,
            as_of_ts
        )
        VALUES
            (
                950002,
                950001,
                950001,
                950001,
                950004,
                'fk-expiry-mismatched-leg',
                TIMESTAMPTZ '2026-04-29 10:00:00+00'
            );
        RAISE EXCEPTION 'expected foreign_key_violation for expiries trade/leg mismatch';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('expiries id_spe and id_leg must point to the same DISC trade');

INSERT INTO leverages_per_trade_snapshots (
    id_leverage_trade_snapshot,
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
        950001,
        950001,
        950001,
        950001,
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'file',
        'loaded',
        1,
        FALSE,
        'FK hardening leverage per trade'
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO leverages_per_trade (
            id_leverage_trade_row,
            id_org,
            id_leverage_trade_snapshot,
            id_f,
            as_of_ts,
            trade_id,
            id_spe,
            id_leg,
            gross_leverage
        )
        VALUES
            (
                950001,
                950001,
                950001,
                950001,
                TIMESTAMPTZ '2026-04-29 10:00:00+00',
                950001,
                950001,
                950004,
                2.50
            );
        RAISE EXCEPTION 'expected foreign_key_violation for leverage trade/leg mismatch';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('leverages_per_trade id_spe and id_leg must point to the same DISC trade');

INSERT INTO leverages_per_underlying_snapshots (
    id_leverage_underlying_snapshot,
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
        950001,
        950001,
        950001,
        950001,
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'file',
        'loaded',
        1,
        FALSE,
        'FK hardening leverage per underlying'
    );

INSERT INTO leverages_per_underlying (
    id_leverage_underlying_row,
    id_org,
    id_leverage_underlying_snapshot,
    id_f,
    as_of_ts,
    underlying_asset,
    gross_leverage
)
VALUES
    (
        950001,
        950001,
        950001,
        950001,
        TIMESTAMPTZ '2026-04-29 10:00:00+00',
        'SPX',
        1.10
    );

DO $$
BEGIN
    BEGIN
        INSERT INTO leverages_per_underlying (
            id_leverage_underlying_row,
            id_org,
            id_leverage_underlying_snapshot,
            id_f,
            as_of_ts,
            underlying_asset,
            gross_leverage
        )
        VALUES
            (
                950002,
                950001,
                950001,
                950001,
                TIMESTAMPTZ '2026-04-29 10:00:00+00',
                'SPX',
                1.20
            );
        RAISE EXCEPTION 'expected unique_violation for duplicate leverage underlying row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('leverages_per_underlying stays unique per snapshot and underlying asset');

SELECT * FROM finish();

ROLLBACK;
