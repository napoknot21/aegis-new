BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET search_path = extensions, public;

SELECT plan(7);

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
    (920001, 'TS2', 'Test Trade Currency', 'TS2', 902, 2, 902, TRUE);

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
    (920001, 'TSAC', 'TA', 'Test Asset Class', 'Test asset class for trade legs', 902, TRUE);

INSERT INTO organisations (
    id_org,
    code,
    legal_name,
    display_name
)
VALUES
    (920001, 'TESTORG_TRADE', 'Test Org Trade', 'Test Org Trade');

INSERT INTO offices (
    id_off,
    id_org,
    code,
    name
)
VALUES
    (920001, 920001, 'PAR', 'Paris');

INSERT INTO users (
    id_user,
    id_org,
    entra_oid,
    email,
    display_name
)
VALUES
    (
        920001,
        920001,
        '11111111-1111-1111-1111-111111111111',
        'trade-user@example.com',
        'Trade User'
    );

INSERT INTO funds (
    id_f,
    id_org,
    id_ccy,
    name,
    code
)
VALUES
    (920001, 920001, 920001, 'Trade Fund', 'TRDFUND');

INSERT INTO books (
    id_book,
    id_org,
    name,
    id_f
)
VALUES
    (920001, 920001, 'Main Book', 920001);

INSERT INTO banks (
    id_bank,
    id_org,
    name,
    code
)
VALUES
    (920001, 920001, 'Test Bank', 'TBANK');

INSERT INTO counterparties (
    id_ctpy,
    id_org,
    id_bank,
    ice_name,
    ext_code
)
VALUES
    (920001, 920001, 920001, 'Counterparty One', 'CPONE');

INSERT INTO trade_types (
    id_type,
    id_org,
    name,
    code
)
VALUES
    (920001, 920001, 'Option', 'OPT');

INSERT INTO trade_disc_labels (
    id_label,
    id_org,
    code
)
VALUES
    (920001, 920001, 'DISC');

INSERT INTO trade_spe (
    id_spe,
    id_org
)
VALUES
    (920001, 920001);

INSERT INTO trades (
    id_trade,
    id_org,
    id_spe,
    id_type,
    id_f,
    booked_by,
    status
)
VALUES
    (920001, 920001, 920001, 920001, 920001, 920001, 'booked');

INSERT INTO trade_disc (
    id_spe,
    id_org,
    id_book,
    id_ctpy,
    id_label,
    trade_name,
    trade_date
)
VALUES
    (920001, 920001, 920001, 920001, 920001, 'Trade 123', DATE '2026-04-14');

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
    (920011, 920001, 920001, 920001, '1231', 'Buy', 100.00, 920001),
    (920012, 920001, 920001, 920001, '1232', 'Sell', 50.00, 920001);

SELECT is(
    (SELECT COUNT(*)::INT FROM trade_disc_legs WHERE id_org = 920001 AND id_disc = 920001),
    2,
    'one trade_disc can own multiple legs'
);

INSERT INTO trade_disc_instruments (
    id_inst,
    id_org,
    id_leg,
    id_ac,
    notional,
    id_ccy,
    buysell,
    i_type,
    trade_date
)
VALUES
    (920021, 920001, 920011, 920001, 100.00, 920001, 'Buy', 'Option', DATE '2026-04-14');

INSERT INTO trade_disc_fields (
    id_field,
    id_org,
    id_leg,
    id_ccy,
    d_date,
    notional,
    payout_ccy_id,
    buysell,
    i_type
)
VALUES
    (920031, 920001, 920011, 920001, DATE '2026-04-14', 100.00, 920001, 'Buy', 'Option');

INSERT INTO trade_disc_premiums (
    id_prem,
    id_org,
    id_leg,
    amount,
    id_ccy,
    p_date
)
VALUES
    (920041, 920001, 920011, 3.50, 920001, DATE '2026-04-14');

INSERT INTO trade_disc_settlements (
    id_settle,
    id_org,
    id_leg,
    s_date,
    id_ccy,
    type
)
VALUES
    (920051, 920001, 920011, DATE '2026-04-15', 920001, 'cash');

DO $$
BEGIN
    BEGIN
        INSERT INTO trade_disc_instruments (
            id_inst,
            id_org,
            id_leg,
            id_ac,
            notional,
            id_ccy,
            buysell
        )
        VALUES (920022, 920001, 920011, 920001, 10.00, 920001, 'Buy');
        RAISE EXCEPTION 'expected unique_violation for duplicate trade_disc_instruments row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('trade_disc_instruments stays 1:1 with each leg');

DO $$
BEGIN
    BEGIN
        INSERT INTO trade_disc_fields (
            id_field,
            id_org,
            id_leg
        )
        VALUES (920032, 920001, 920011);
        RAISE EXCEPTION 'expected unique_violation for duplicate trade_disc_fields row';
    EXCEPTION
        WHEN unique_violation THEN
            NULL;
    END;
END $$;

SELECT pass('trade_disc_fields stays 1:1 with each leg');

DELETE FROM trade_disc_legs
WHERE id_org = 920001
  AND id_leg = 920011;

SELECT is(
    (SELECT COUNT(*)::INT FROM trade_disc_instruments WHERE id_org = 920001 AND id_leg = 920011),
    0,
    'deleting a leg cascades to trade_disc_instruments'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM trade_disc_fields WHERE id_org = 920001 AND id_leg = 920011),
    0,
    'deleting a leg cascades to trade_disc_fields'
);

SELECT is(
    (
        SELECT COUNT(*)::INT
        FROM trade_disc_premiums
        WHERE id_org = 920001
          AND id_leg = 920011
    ) +
    (
        SELECT COUNT(*)::INT
        FROM trade_disc_settlements
        WHERE id_org = 920001
          AND id_leg = 920011
    ),
    0,
    'deleting a leg cascades to the other optional leg child tables too'
);

SELECT is(
    (SELECT COUNT(*)::INT FROM trade_disc_legs WHERE id_org = 920001 AND id_disc = 920001),
    1,
    'other legs on the trade remain intact after deleting one leg'
);

SELECT * FROM finish();

ROLLBACK;
