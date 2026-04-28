BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(18);

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
    (940001, 'TS4', 'Test Ingestion Currency 1', 'TS4', 904, 2, 904, TRUE),
    (940002, 'TS5', 'Test Ingestion Currency 2', 'TS5', 905, 2, 905, TRUE);

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
    (940001, 'TPI', 'TPI', 'Test Pipeline Asset Class', 'Test asset class for ingestion pipeline', 904, TRUE);

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (940001, 'TESTORG_PIPE', 'Test Org Pipeline', 'Test Org Pipeline');

INSERT INTO funds (
    id_f,
    id_org,
    id_ccy,
    name,
    code
)
VALUES
    (940001, 940001, 940001, 'Pipeline Fund A', 'PIPEFUNDA'),
    (940002, 940001, 940001, 'Pipeline Fund B', 'PIPEFUNDB');

INSERT INTO banks (
    id_bank,
    id_org,
    name,
    code
)
VALUES
    (940001, 940001, 'Pipeline Bank', 'PIPEBANK');

INSERT INTO counterparties (
    id_ctpy,
    id_org,
    id_bank,
    ice_name,
    ext_code
)
VALUES
    (940001, 940001, 940001, 'Pipeline Counterparty', 'PIPECP');

INSERT INTO books (
    id_book,
    id_org,
    name,
    id_f
)
VALUES
    (940001, 940001, 'Pipeline Book', 940001);

INSERT INTO trade_types (
    id_type,
    id_org,
    name,
    code
)
VALUES
    (940001, 940001, 'Pipeline Option', 'POPT');

INSERT INTO trade_disc_labels (
    id_label,
    id_org,
    code
)
VALUES
    (940001, 940001, 'PIPE');

INSERT INTO ingestion_sources (
    id_source,
    id_org,
    code,
    name,
    description
)
VALUES
    (
        940001,
        940001,
        'ice_excel_multi',
        'ICE Excel multi-file',
        'Three-file test source'
    );

INSERT INTO ingestion_runs (
    id_ingestion_run,
    id_org,
    id_f,
    id_run,
    id_source,
    run_type,
    snapshot_ts,
    source_name,
    status,
    notes
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        940001,
        'reporting_snapshot',
        TIMESTAMPTZ '2026-04-28 10:00:00+00',
        'ice_excel_multi',
        'loaded',
        'ingestion pipeline schema test run'
    );

INSERT INTO trade_spe (
    id_spe,
    id_org
)
VALUES
    (940001, 940001);

INSERT INTO trades (
    id_trade,
    id_org,
    id_spe,
    id_type,
    id_f,
    status
)
VALUES
    (940001, 940001, 940001, 940001, 940001, 'booked');

INSERT INTO trade_disc (
    id_spe,
    id_org,
    id_book,
    id_ctpy,
    id_label,
    ice_trade_id,
    trade_name,
    trade_date
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        940001,
        'ICE-TRADE-940001',
        'Pipeline Trade',
        DATE '2026-04-28'
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
    (940001, 940001, 940001, 940001, 'ICE-LEG-940001', 'Buy', 100.00, 940001);

INSERT INTO fx_rates (
    id_fx_rate,
    id_ccy_from,
    id_ccy_to,
    rate_date,
    rate,
    source
)
VALUES
    (940001, 940001, 940002, DATE '2026-04-28', 1.23450000, NULL);

SELECT is(
    (
        SELECT rate
        FROM fx_rates
        WHERE id_fx_rate = 940001
    ),
    1.23450000::NUMERIC,
    'fx_rates stores a global nullable-source rate'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO fx_rates (
            id_fx_rate,
            id_ccy_from,
            id_ccy_to,
            rate_date,
            rate,
            source
        )
        VALUES
            (940002, 940001, 940002, DATE '2026-04-28', 1.25000000, NULL);
        RAISE EXCEPTION 'expected unique_violation for duplicate null-source fx rate';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('fx_rates treats NULL source as a unique-source value');

SELECT is(
    (
        SELECT id_source
        FROM ingestion_runs
        WHERE id_ingestion_run = 940001
    ),
    940001::BIGINT,
    'ingestion_runs records the source that produced the run'
);

SELECT ok(
    (
        SELECT status = 'active'
           AND first_seen_at IS NOT NULL
           AND last_seen_at IS NOT NULL
        FROM trade_disc_legs
        WHERE id_leg = 940001
    ),
    'trade_disc_legs lifecycle defaults are populated'
);

SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'trg_trade_disc_set_updated_at'
          AND tgrelid = 'trade_disc'::regclass
          AND NOT tgisinternal
    ),
    'trade_disc has an updated_at trigger'
);

UPDATE trade_disc_legs
SET status = 'disappeared'
WHERE id_leg = 940001;

SELECT ok(
    (
        SELECT status_updated_at IS NOT NULL
        FROM trade_disc_legs
        WHERE id_leg = 940001
    ),
    'trade_disc_legs marks status change time'
);

INSERT INTO raw_ingestion_payloads (
    id_payload,
    id_org,
    id_f,
    id_source,
    id_ingestion_run,
    payload_type,
    file_role,
    file_name,
    storage_path,
    file_checksum,
    source_ts,
    row_count_raw
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        940001,
        'file',
        'trade_legs',
        'Trade Legs - 2026-04-28T100000.xlsx',
        'raw/940001/trade-legs.xlsx',
        'sha256-payload-940001',
        TIMESTAMPTZ '2026-04-28 10:00:00+00',
        1
    );

SELECT is(
    (
        SELECT payload_type
        FROM raw_ingestion_payloads
        WHERE id_payload = 940001
    ),
    'file',
    'raw_ingestion_payloads stores file payload metadata'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO raw_ingestion_payloads (
            id_payload,
            id_org,
            id_f,
            id_source,
            id_ingestion_run,
            payload_type,
            file_checksum
        )
        VALUES
            (940002, 940001, 940002, 940001, 940001, 'file', 'sha256-mismatch');
        RAISE EXCEPTION 'expected foreign_key_violation for payload/run fund mismatch';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('raw_ingestion_payloads enforces run fund alignment');

INSERT INTO ingestion_field_mappings (
    id_mapping,
    id_org,
    id_source,
    target_table,
    target_column,
    source_field,
    transform_type,
    lookup_table,
    lookup_column,
    is_required
)
VALUES
    (
        940001,
        940001,
        940001,
        'trade_disc',
        'id_ctpy',
        'Counterparty',
        'lookup',
        'counterparties',
        'ice_name',
        TRUE
    );

SELECT is(
    (
        SELECT lookup_table
        FROM ingestion_field_mappings
        WHERE id_mapping = 940001
    ),
    'counterparties',
    'ingestion_field_mappings stores lookup rules'
);

INSERT INTO trade_leg_diffs (
    id_diff,
    id_org,
    id_f,
    id_ingestion_run,
    id_leg,
    ice_leg_id,
    diff_type,
    changed_columns,
    snapshot_before,
    snapshot_after
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        940001,
        'ICE-LEG-940001',
        'modified',
        ARRAY['notional'],
        '{"notional": 90.0}'::JSONB,
        '{"notional": 100.0}'::JSONB
    );

SELECT is(
    (
        SELECT diff_type
        FROM trade_leg_diffs
        WHERE id_diff = 940001
    ),
    'modified',
    'trade_leg_diffs links a leg diff to the ingestion run'
);

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
        940001,
        940001,
        940001,
        940001,
        DATE '2026-04-28',
        TIMESTAMPTZ '2026-04-28 10:00:00+00',
        'expiries.csv',
        'loaded',
        1,
        TRUE,
        'expiry links test'
    );

INSERT INTO expiries (
    id_exp_row,
    id_org,
    id_exp_snapshot,
    id_spe,
    id_leg,
    ice_trade_id,
    ice_leg_id,
    row_hash,
    as_of_ts
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        940001,
        'ICE-TRADE-940001',
        'ICE-LEG-940001',
        'exp-940001',
        TIMESTAMPTZ '2026-04-28 10:00:00+00'
    );

SELECT is(
    (
        SELECT id_leg
        FROM expiries
        WHERE id_exp_row = 940001
    ),
    940001::BIGINT,
    'expiries can link back to the source trade leg'
);

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
        940001,
        940001,
        940001,
        940001,
        TIMESTAMPTZ '2026-04-28 10:00:00+00',
        'file',
        'loaded',
        1,
        FALSE,
        'leverage trade links test'
    );

INSERT INTO leverages_per_trade (
    id_leverage_trade_row,
    id_org,
    id_leverage_trade_snapshot,
    id_f,
    as_of_ts,
    trade_id,
    id_spe,
    id_leg,
    ice_trade_id,
    ice_leg_id,
    gross_leverage
)
VALUES
    (
        940001,
        940001,
        940001,
        940001,
        TIMESTAMPTZ '2026-04-28 10:00:00+00',
        940001,
        940001,
        940001,
        'ICE-TRADE-940001',
        'ICE-LEG-940001',
        2.50
    );

SELECT is(
    (
        SELECT id_spe
        FROM leverages_per_trade
        WHERE id_leverage_trade_row = 940001
    ),
    940001::BIGINT,
    'leverages_per_trade can link back to the source trade'
);

SELECT is(
    (
        SELECT id_leg
        FROM leverages_per_trade
        WHERE id_leverage_trade_row = 940001
    ),
    940001::BIGINT,
    'leverages_per_trade can link back to the source trade leg'
);

DELETE FROM ingestion_runs
WHERE id_ingestion_run = 940001;

SELECT ok(
    (
        SELECT id_ingestion_run IS NULL
        FROM raw_ingestion_payloads
        WHERE id_payload = 940001
    ),
    'raw_ingestion_payloads keep audit metadata when the run is deleted'
);

SELECT is(
    (
        SELECT COUNT(*)::INT
        FROM trade_leg_diffs
        WHERE id_org = 940001
    ),
    0,
    'trade_leg_diffs cascade when the parent run is deleted'
);

INSERT INTO trade_spe (
    id_spe,
    id_org
)
VALUES
    (940002, 940001);

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
            (940002, 940001, 940001, 940001, 940001, 'ICE-TRADE-ORPHAN');
        RAISE EXCEPTION 'expected foreign_key_violation for trade_disc without trades parent';
    EXCEPTION
        WHEN foreign_key_violation THEN
            NULL;
    END;
END $$;

SELECT pass('trade_disc requires the trades parent row');

SELECT is(
    (
        SELECT COUNT(*)::INT
        FROM pg_constraint
        WHERE conrelid = 'trade_disc'::regclass
          AND conname = 'fk_disc_spe'
    ),
    0,
    'old trade_disc -> trade_spe FK has been removed'
);

SELECT ok(
    has_table_privilege('service_role', 'public.raw_ingestion_payloads', 'SELECT')
    AND NOT has_table_privilege('anon', 'public.raw_ingestion_payloads', 'SELECT'),
    'new ingestion tables follow the service-role-only access posture'
);

SELECT * FROM finish();

ROLLBACK;
