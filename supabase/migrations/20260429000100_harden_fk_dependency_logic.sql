-- ============================================================
-- AEGIS - harden foreign-key dependency logic
-- Purpose:
--   - keep book hierarchies inside one fund
--   - carry fund identity down the DISC trade tree
--   - keep reporting trade links aligned with their snapshot fund
--   - close missing row-grain constraints
-- ============================================================


-- ============================================================
-- BOOK HIERARCHY: PARENT MUST BELONG TO THE SAME FUND
-- ============================================================

ALTER TABLE books
    DROP CONSTRAINT IF EXISTS fk_book_parent;

ALTER TABLE books
    DROP CONSTRAINT IF EXISTS uq_books_org_fund_book;
ALTER TABLE books
    ADD CONSTRAINT uq_books_org_fund_book
    UNIQUE (id_org, id_f, id_book);

ALTER TABLE books
    ADD CONSTRAINT fk_book_parent
    FOREIGN KEY (id_org, id_f, parent_id)
    REFERENCES books(id_org, id_f, id_book);

CREATE INDEX IF NOT EXISTS idx_books_fund_parent
    ON books(id_org, id_f, parent_id);


-- ============================================================
-- DISC TRADE DETAILS: FUND MUST MATCH THE TRADE HEADER
-- ============================================================

ALTER TABLE trades
    DROP CONSTRAINT IF EXISTS uq_trades_org_fund_spe;
ALTER TABLE trades
    ADD CONSTRAINT uq_trades_org_fund_spe
    UNIQUE (id_org, id_f, id_spe);

ALTER TABLE trade_disc
    ADD COLUMN IF NOT EXISTS id_f BIGINT;

UPDATE trade_disc AS disc
SET id_f = trade.id_f
FROM trades AS trade
WHERE trade.id_org = disc.id_org
  AND trade.id_spe = disc.id_spe
  AND disc.id_f IS DISTINCT FROM trade.id_f;

CREATE OR REPLACE FUNCTION set_trade_disc_fund_from_trade()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    parent_fund_id BIGINT;
BEGIN
    SELECT trade.id_f
    INTO parent_fund_id
    FROM trades AS trade
    WHERE trade.id_org = NEW.id_org
      AND trade.id_spe = NEW.id_spe;

    IF parent_fund_id IS NULL THEN
        RAISE EXCEPTION 'trade_disc row (id_org %, id_spe %) has no parent trade', NEW.id_org, NEW.id_spe
            USING ERRCODE = '23503';
    END IF;

    IF NEW.id_f IS NOT NULL AND NEW.id_f <> parent_fund_id THEN
        RAISE EXCEPTION 'trade_disc fund % does not match parent trade fund %', NEW.id_f, parent_fund_id
            USING ERRCODE = '23503';
    END IF;

    NEW.id_f = parent_fund_id;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_trade_disc_set_fund ON trade_disc;
CREATE TRIGGER trg_trade_disc_set_fund
BEFORE INSERT OR UPDATE OF id_org, id_spe, id_f ON trade_disc
FOR EACH ROW
EXECUTE FUNCTION set_trade_disc_fund_from_trade();

ALTER TABLE trade_disc
    ALTER COLUMN id_f SET NOT NULL;

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_spe;

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_trade;
ALTER TABLE trade_disc
    ADD CONSTRAINT fk_disc_trade
    FOREIGN KEY (id_org, id_f, id_spe)
    REFERENCES trades(id_org, id_f, id_spe);

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS uq_trade_disc_org_fund_spe;
ALTER TABLE trade_disc
    ADD CONSTRAINT uq_trade_disc_org_fund_spe
    UNIQUE (id_org, id_f, id_spe);

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_book;
ALTER TABLE trade_disc
    ADD CONSTRAINT fk_disc_book
    FOREIGN KEY (id_org, id_f, id_book)
    REFERENCES books(id_org, id_f, id_book);

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_portfolio;
ALTER TABLE trade_disc
    ADD CONSTRAINT fk_disc_portfolio
    FOREIGN KEY (id_org, id_f, id_portfolio)
    REFERENCES books(id_org, id_f, id_book);

CREATE INDEX IF NOT EXISTS idx_trade_disc_fund
    ON trade_disc(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_trade_disc_fund_book
    ON trade_disc(id_org, id_f, id_book);
CREATE INDEX IF NOT EXISTS idx_trade_disc_fund_portfolio
    ON trade_disc(id_org, id_f, id_portfolio)
    WHERE id_portfolio IS NOT NULL;


-- ============================================================
-- DISC LEGS: FUND MUST MATCH THE DISC TRADE
-- ============================================================

ALTER TABLE trade_disc_legs
    ADD COLUMN IF NOT EXISTS id_f BIGINT;

UPDATE trade_disc_legs AS leg
SET id_f = disc.id_f
FROM trade_disc AS disc
WHERE disc.id_org = leg.id_org
  AND disc.id_spe = leg.id_disc
  AND leg.id_f IS DISTINCT FROM disc.id_f;

CREATE OR REPLACE FUNCTION set_trade_disc_leg_fund_from_disc()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    parent_fund_id BIGINT;
BEGIN
    SELECT disc.id_f
    INTO parent_fund_id
    FROM trade_disc AS disc
    WHERE disc.id_org = NEW.id_org
      AND disc.id_spe = NEW.id_disc;

    IF parent_fund_id IS NULL THEN
        RAISE EXCEPTION 'trade_disc_legs row (id_org %, id_disc %) has no parent DISC trade', NEW.id_org, NEW.id_disc
            USING ERRCODE = '23503';
    END IF;

    IF NEW.id_f IS NOT NULL AND NEW.id_f <> parent_fund_id THEN
        RAISE EXCEPTION 'trade_disc_legs fund % does not match parent DISC fund %', NEW.id_f, parent_fund_id
            USING ERRCODE = '23503';
    END IF;

    NEW.id_f = parent_fund_id;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_trade_disc_legs_set_fund ON trade_disc_legs;
CREATE TRIGGER trg_trade_disc_legs_set_fund
BEFORE INSERT OR UPDATE OF id_org, id_disc, id_f ON trade_disc_legs
FOR EACH ROW
EXECUTE FUNCTION set_trade_disc_leg_fund_from_disc();

ALTER TABLE trade_disc_legs
    ALTER COLUMN id_f SET NOT NULL;

ALTER TABLE trade_disc_legs
    DROP CONSTRAINT IF EXISTS fk_leg_disc;
ALTER TABLE trade_disc_legs
    ADD CONSTRAINT fk_leg_disc
    FOREIGN KEY (id_org, id_f, id_disc)
    REFERENCES trade_disc(id_org, id_f, id_spe);

ALTER TABLE trade_disc_legs
    DROP CONSTRAINT IF EXISTS uq_trade_disc_legs_org_fund_leg;
ALTER TABLE trade_disc_legs
    ADD CONSTRAINT uq_trade_disc_legs_org_fund_leg
    UNIQUE (id_org, id_f, id_leg);

ALTER TABLE trade_disc_legs
    DROP CONSTRAINT IF EXISTS uq_trade_disc_legs_org_fund_disc_leg;
ALTER TABLE trade_disc_legs
    ADD CONSTRAINT uq_trade_disc_legs_org_fund_disc_leg
    UNIQUE (id_org, id_f, id_disc, id_leg);

CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_fund
    ON trade_disc_legs(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_trade_disc_legs_fund_disc
    ON trade_disc_legs(id_org, id_f, id_disc);


-- ============================================================
-- EXPIRIES: FUND MUST MATCH THE SNAPSHOT AND LINKED TRADE
-- ============================================================

ALTER TABLE expiries_snapshots
    DROP CONSTRAINT IF EXISTS uq_exp_snapshots_row_match;
ALTER TABLE expiries_snapshots
    ADD CONSTRAINT uq_exp_snapshots_row_match
    UNIQUE (id_org, id_exp_snapshot, id_f);

ALTER TABLE expiries
    ADD COLUMN IF NOT EXISTS id_f BIGINT;

UPDATE expiries AS expiry
SET id_f = snapshot.id_f
FROM expiries_snapshots AS snapshot
WHERE snapshot.id_org = expiry.id_org
  AND snapshot.id_exp_snapshot = expiry.id_exp_snapshot
  AND expiry.id_f IS DISTINCT FROM snapshot.id_f;

CREATE OR REPLACE FUNCTION set_expiry_row_fund_from_snapshot()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    snapshot_fund_id BIGINT;
BEGIN
    SELECT snapshot.id_f
    INTO snapshot_fund_id
    FROM expiries_snapshots AS snapshot
    WHERE snapshot.id_org = NEW.id_org
      AND snapshot.id_exp_snapshot = NEW.id_exp_snapshot;

    IF snapshot_fund_id IS NULL THEN
        RAISE EXCEPTION 'expiries row (id_org %, id_exp_snapshot %) has no parent snapshot', NEW.id_org, NEW.id_exp_snapshot
            USING ERRCODE = '23503';
    END IF;

    IF NEW.id_f IS NOT NULL AND NEW.id_f <> snapshot_fund_id THEN
        RAISE EXCEPTION 'expiries row fund % does not match parent snapshot fund %', NEW.id_f, snapshot_fund_id
            USING ERRCODE = '23503';
    END IF;

    NEW.id_f = snapshot_fund_id;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_expiries_set_fund ON expiries;
CREATE TRIGGER trg_expiries_set_fund
BEFORE INSERT OR UPDATE OF id_org, id_exp_snapshot, id_f ON expiries
FOR EACH ROW
EXECUTE FUNCTION set_expiry_row_fund_from_snapshot();

ALTER TABLE expiries
    ALTER COLUMN id_f SET NOT NULL;

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_row_snapshot_match;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_row_snapshot_match
    FOREIGN KEY (id_org, id_exp_snapshot, id_f)
    REFERENCES expiries_snapshots(id_org, id_exp_snapshot, id_f)
    ON DELETE CASCADE;

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_spe;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_spe
    FOREIGN KEY (id_org, id_f, id_spe)
    REFERENCES trades(id_org, id_f, id_spe);

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_leg;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_leg
    FOREIGN KEY (id_org, id_f, id_leg)
    REFERENCES trade_disc_legs(id_org, id_f, id_leg);

ALTER TABLE expiries
    DROP CONSTRAINT IF EXISTS fk_exp_trade_leg_match;
ALTER TABLE expiries
    ADD CONSTRAINT fk_exp_trade_leg_match
    FOREIGN KEY (id_org, id_f, id_spe, id_leg)
    REFERENCES trade_disc_legs(id_org, id_f, id_disc, id_leg);

CREATE INDEX IF NOT EXISTS idx_expiries_fund
    ON expiries(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_expiries_fund_spe
    ON expiries(id_org, id_f, id_spe)
    WHERE id_spe IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_expiries_fund_leg
    ON expiries(id_org, id_f, id_leg)
    WHERE id_leg IS NOT NULL;


-- ============================================================
-- LEVERAGE PER TRADE: LINKED TRADE AND LEG MUST MATCH THE FUND
-- ============================================================

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_lev_trade_spe;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_lev_trade_spe
    FOREIGN KEY (id_org, id_f, id_spe)
    REFERENCES trades(id_org, id_f, id_spe);

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_lev_trade_leg;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_lev_trade_leg
    FOREIGN KEY (id_org, id_f, id_leg)
    REFERENCES trade_disc_legs(id_org, id_f, id_leg);

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_lev_trade_leg_spe_match;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_lev_trade_leg_spe_match
    FOREIGN KEY (id_org, id_f, id_spe, id_leg)
    REFERENCES trade_disc_legs(id_org, id_f, id_disc, id_leg);

CREATE INDEX IF NOT EXISTS idx_lev_trade_fund_spe
    ON leverages_per_trade(id_org, id_f, id_spe)
    WHERE id_spe IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lev_trade_fund_leg
    ON leverages_per_trade(id_org, id_f, id_leg)
    WHERE id_leg IS NOT NULL;


-- ============================================================
-- LEG DIFFS: DIFF FUND MUST MATCH THE LINKED LEG FUND
-- ============================================================

ALTER TABLE trade_leg_diffs
    DROP CONSTRAINT IF EXISTS fk_diff_leg;
ALTER TABLE trade_leg_diffs
    ADD CONSTRAINT fk_diff_leg
    FOREIGN KEY (id_org, id_f, id_leg)
    REFERENCES trade_disc_legs(id_org, id_f, id_leg);

CREATE INDEX IF NOT EXISTS idx_leg_diffs_fund_leg
    ON trade_leg_diffs(id_org, id_f, id_leg)
    WHERE id_leg IS NOT NULL;


-- ============================================================
-- LEVERAGE PER UNDERLYING: ONE ROW PER UNDERLYING PER SNAPSHOT
-- ============================================================

ALTER TABLE leverages_per_underlying
    DROP CONSTRAINT IF EXISTS uq_leverages_underlying_snapshot_underlying;
ALTER TABLE leverages_per_underlying
    ADD CONSTRAINT uq_leverages_underlying_snapshot_underlying
    UNIQUE NULLS NOT DISTINCT (id_org, id_leverage_underlying_snapshot, underlying_asset);


-- ============================================================
-- LOCKDOWN CONSISTENCY FOR ROUTINES CREATED IN THIS MIGRATION
-- ============================================================

REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;
