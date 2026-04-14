-- ============================================================
-- AEGIS - harden schema coherence
-- Purpose:
--   - enforce single-primary assignment semantics
--   - strengthen trade header/detail consistency
--   - tighten reporting row grain and header/row alignment
--   - keep updated_at columns synchronized on updates
-- ============================================================


-- ============================================================
-- UPDATED_AT AUTOMATION
-- ============================================================

CREATE OR REPLACE FUNCTION set_row_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_currencies_set_updated_at ON currencies;
CREATE TRIGGER trg_currencies_set_updated_at
BEFORE UPDATE ON currencies
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_asset_classes_set_updated_at ON asset_classes;
CREATE TRIGGER trg_asset_classes_set_updated_at
BEFORE UPDATE ON asset_classes
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_organisations_set_updated_at ON organisations;
CREATE TRIGGER trg_organisations_set_updated_at
BEFORE UPDATE ON organisations
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_offices_set_updated_at ON offices;
CREATE TRIGGER trg_offices_set_updated_at
BEFORE UPDATE ON offices
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_departments_set_updated_at ON departments;
CREATE TRIGGER trg_departments_set_updated_at
BEFORE UPDATE ON departments
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_office_departments_set_updated_at ON office_departments;
CREATE TRIGGER trg_office_departments_set_updated_at
BEFORE UPDATE ON office_departments
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_users_set_updated_at ON users;
CREATE TRIGGER trg_users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_user_offices_set_updated_at ON user_offices;
CREATE TRIGGER trg_user_offices_set_updated_at
BEFORE UPDATE ON user_offices
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_user_departments_set_updated_at ON user_departments;
CREATE TRIGGER trg_user_departments_set_updated_at
BEFORE UPDATE ON user_departments
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_ranks_set_updated_at ON ranks;
CREATE TRIGGER trg_ranks_set_updated_at
BEFORE UPDATE ON ranks
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();

DROP TRIGGER IF EXISTS trg_access_roles_set_updated_at ON access_roles;
CREATE TRIGGER trg_access_roles_set_updated_at
BEFORE UPDATE ON access_roles
FOR EACH ROW
EXECUTE FUNCTION set_row_updated_at();


-- ============================================================
-- SINGLE-PRIMARY / NORMALIZED EMAIL GUARANTEES
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_office_departments_primary_active
    ON office_departments(id_org, id_off)
    WHERE is_primary AND is_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_offices_primary_active
    ON user_offices(id_org, id_user)
    WHERE is_primary AND is_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_departments_primary_active
    ON user_departments(id_org, id_user)
    WHERE is_primary AND is_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_ranks_primary_active
    ON user_ranks(id_org, id_user)
    WHERE is_primary AND is_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fund_office_access_primary_active
    ON fund_office_access(id_org, id_f)
    WHERE access_type = 'primary' AND is_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_org_email_ci
    ON users(id_org, lower(email));


-- ============================================================
-- TRADE COHERENCE
-- ============================================================

ALTER TABLE trades
    DROP CONSTRAINT IF EXISTS uq_trades_org_spe;
ALTER TABLE trades
    ADD CONSTRAINT uq_trades_org_spe UNIQUE (id_org, id_spe);

ALTER TABLE trade_disc
    DROP CONSTRAINT IF EXISTS fk_disc_trade;
ALTER TABLE trade_disc
    ADD CONSTRAINT fk_disc_trade
    FOREIGN KEY (id_org, id_spe)
    REFERENCES trades(id_org, id_spe);

ALTER TABLE trade_disc_fields
    DROP CONSTRAINT IF EXISTS trade_disc_fields_buysell_check;
ALTER TABLE trade_disc_fields
    ADD CONSTRAINT trade_disc_fields_buysell_check
    CHECK (buysell IS NULL OR buysell IN ('Buy', 'Sell'));


-- ============================================================
-- REPORTING GRAIN
-- ============================================================

ALTER TABLE simm_snapshots
    DROP CONSTRAINT IF EXISTS simm_snapshots_id_org_id_f_as_of_date_is_official_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_simm_snapshots_official_per_day
    ON simm_snapshots(id_org, id_f, as_of_date)
    WHERE is_official;

ALTER TABLE nav_estimated
    DROP CONSTRAINT IF EXISTS uq_nav_estimated_one_row_per_snapshot;
ALTER TABLE nav_estimated
    ADD CONSTRAINT uq_nav_estimated_one_row_per_snapshot
    UNIQUE (id_org, id_nav_est_snapshot);

ALTER TABLE leverages
    DROP CONSTRAINT IF EXISTS uq_leverages_one_row_per_snapshot;
ALTER TABLE leverages
    ADD CONSTRAINT uq_leverages_one_row_per_snapshot
    UNIQUE (id_org, id_leverage_snapshot);

ALTER TABLE long_short_delta
    DROP CONSTRAINT IF EXISTS uq_long_short_delta_snapshot_underlying;
ALTER TABLE long_short_delta
    ADD CONSTRAINT uq_long_short_delta_snapshot_underlying
    UNIQUE (id_org, id_long_short_delta_snapshot, underlying_asset);

ALTER TABLE counterparty_concentration
    DROP CONSTRAINT IF EXISTS uq_counterparty_concentration_snapshot_ctpy;
ALTER TABLE counterparty_concentration
    ADD CONSTRAINT uq_counterparty_concentration_snapshot_ctpy
    UNIQUE (id_org, id_ctpy_concentration_snapshot, id_ctpy);


-- ============================================================
-- REPORTING HEADER/ROW MATCHING
-- ============================================================

ALTER TABLE simm_snapshots
    DROP CONSTRAINT IF EXISTS uq_simm_snapshots_row_match;
ALTER TABLE simm_snapshots
    ADD CONSTRAINT uq_simm_snapshots_row_match
    UNIQUE (id_org, id_simm_snapshot, id_f, as_of_date);

ALTER TABLE nav_estimated_snapshots
    DROP CONSTRAINT IF EXISTS uq_nav_est_snapshots_row_match;
ALTER TABLE nav_estimated_snapshots
    ADD CONSTRAINT uq_nav_est_snapshots_row_match
    UNIQUE (id_org, id_nav_est_snapshot, id_f);

ALTER TABLE leverages_snapshots
    DROP CONSTRAINT IF EXISTS uq_leverage_snapshots_row_match;
ALTER TABLE leverages_snapshots
    ADD CONSTRAINT uq_leverage_snapshots_row_match
    UNIQUE (id_org, id_leverage_snapshot, id_f);

ALTER TABLE leverages_per_trade_snapshots
    DROP CONSTRAINT IF EXISTS uq_leverage_trade_snapshots_row_match;
ALTER TABLE leverages_per_trade_snapshots
    ADD CONSTRAINT uq_leverage_trade_snapshots_row_match
    UNIQUE (id_org, id_leverage_trade_snapshot, id_f);

ALTER TABLE leverages_per_underlying_snapshots
    DROP CONSTRAINT IF EXISTS uq_leverage_underlying_snapshots_row_match;
ALTER TABLE leverages_per_underlying_snapshots
    ADD CONSTRAINT uq_leverage_underlying_snapshots_row_match
    UNIQUE (id_org, id_leverage_underlying_snapshot, id_f);

ALTER TABLE long_short_delta_snapshots
    DROP CONSTRAINT IF EXISTS uq_long_short_delta_snapshots_row_match;
ALTER TABLE long_short_delta_snapshots
    ADD CONSTRAINT uq_long_short_delta_snapshots_row_match
    UNIQUE (id_org, id_long_short_delta_snapshot, id_f, as_of_ts);

ALTER TABLE counterparty_concentration_snapshots
    DROP CONSTRAINT IF EXISTS uq_ctpy_concentration_snapshots_row_match;
ALTER TABLE counterparty_concentration_snapshots
    ADD CONSTRAINT uq_ctpy_concentration_snapshots_row_match
    UNIQUE (id_org, id_ctpy_concentration_snapshot, id_f, as_of_ts);

ALTER TABLE simm_snapshot_rows
    DROP CONSTRAINT IF EXISTS fk_simm_row_snapshot_match;
ALTER TABLE simm_snapshot_rows
    ADD CONSTRAINT fk_simm_row_snapshot_match
    FOREIGN KEY (id_org, id_simm_snapshot, id_f, as_of_date)
    REFERENCES simm_snapshots(id_org, id_simm_snapshot, id_f, as_of_date);

ALTER TABLE nav_estimated
    DROP CONSTRAINT IF EXISTS fk_nav_est_row_snapshot_match;
ALTER TABLE nav_estimated
    ADD CONSTRAINT fk_nav_est_row_snapshot_match
    FOREIGN KEY (id_org, id_nav_est_snapshot, id_f)
    REFERENCES nav_estimated_snapshots(id_org, id_nav_est_snapshot, id_f);

ALTER TABLE leverages
    DROP CONSTRAINT IF EXISTS fk_leverage_row_snapshot_match;
ALTER TABLE leverages
    ADD CONSTRAINT fk_leverage_row_snapshot_match
    FOREIGN KEY (id_org, id_leverage_snapshot, id_f)
    REFERENCES leverages_snapshots(id_org, id_leverage_snapshot, id_f);

ALTER TABLE leverages_per_trade
    DROP CONSTRAINT IF EXISTS fk_leverage_trade_row_snapshot_match;
ALTER TABLE leverages_per_trade
    ADD CONSTRAINT fk_leverage_trade_row_snapshot_match
    FOREIGN KEY (id_org, id_leverage_trade_snapshot, id_f)
    REFERENCES leverages_per_trade_snapshots(id_org, id_leverage_trade_snapshot, id_f);

ALTER TABLE leverages_per_underlying
    DROP CONSTRAINT IF EXISTS fk_leverage_underlying_row_snapshot_match;
ALTER TABLE leverages_per_underlying
    ADD CONSTRAINT fk_leverage_underlying_row_snapshot_match
    FOREIGN KEY (id_org, id_leverage_underlying_snapshot, id_f)
    REFERENCES leverages_per_underlying_snapshots(id_org, id_leverage_underlying_snapshot, id_f);

ALTER TABLE long_short_delta
    DROP CONSTRAINT IF EXISTS fk_long_short_delta_row_snapshot_match;
ALTER TABLE long_short_delta
    ADD CONSTRAINT fk_long_short_delta_row_snapshot_match
    FOREIGN KEY (id_org, id_long_short_delta_snapshot, id_f, as_of_ts)
    REFERENCES long_short_delta_snapshots(id_org, id_long_short_delta_snapshot, id_f, as_of_ts);

ALTER TABLE counterparty_concentration
    DROP CONSTRAINT IF EXISTS fk_ctpy_concentration_row_snapshot_match;
ALTER TABLE counterparty_concentration
    ADD CONSTRAINT fk_ctpy_concentration_row_snapshot_match
    FOREIGN KEY (id_org, id_ctpy_concentration_snapshot, id_f, as_of_ts)
    REFERENCES counterparty_concentration_snapshots(id_org, id_ctpy_concentration_snapshot, id_f, as_of_ts);
