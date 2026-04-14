-- ============================================================
-- AEGIS - add AUM snapshots
-- Purpose:
--   - store daily AUM pulls with the same snapshot discipline as SIMM
--   - keep one official AUM snapshot per fund/day while allowing retries
--   - preserve raw API payloads for future enrichment
--
-- Assumption for V1:
--   - AUM is a fund-level daily metric, so one row per snapshot is expected.
--   - Additional AUM attributes can stay in raw_payload_json until stabilized.
-- ============================================================

CREATE TABLE IF NOT EXISTS aum_snapshots (

    id_aum_snapshot      BIGSERIAL   PRIMARY KEY,
    uuid                 UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org               BIGINT      NOT NULL,

    id_run               BIGINT      NOT NULL,
    id_f                 BIGINT      NOT NULL,

    as_of_date           DATE        NOT NULL,
    source_name          TEXT        NOT NULL DEFAULT 'libapi',

    source_file_name     TEXT,
    source_generated_at  TIMESTAMPTZ,
    loaded_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status               TEXT        NOT NULL DEFAULT 'loaded'
                         CHECK (status IN ('loaded','validated','official','replaced','failed')),

    row_count            INTEGER     NOT NULL DEFAULT 0,
    is_official          BOOLEAN     NOT NULL DEFAULT FALSE,

    notes                TEXT,

    CONSTRAINT fk_aum_snapshot_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_aum_snapshot_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),

    UNIQUE (uuid),
    UNIQUE (id_org, id_aum_snapshot),
    UNIQUE (id_org, id_aum_snapshot, id_f, as_of_date)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_aum_snapshots_official_per_day
    ON aum_snapshots(id_org, id_f, as_of_date)
    WHERE is_official;

CREATE INDEX IF NOT EXISTS idx_aum_snapshots_org ON aum_snapshots(id_org);
CREATE INDEX IF NOT EXISTS idx_aum_snapshots_fund ON aum_snapshots(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_aum_snapshots_as_of_date ON aum_snapshots(id_org, as_of_date);


CREATE TABLE IF NOT EXISTS aum_rows (

    id_aum_row           BIGSERIAL   PRIMARY KEY,
    uuid                 UUID        NOT NULL DEFAULT uuid_generate_v4(),
    id_org               BIGINT      NOT NULL,

    id_aum_snapshot      BIGINT      NOT NULL,
    id_f                 BIGINT      NOT NULL,
    as_of_date           DATE        NOT NULL,

    aum_value            NUMERIC(18,6),
    id_ccy               BIGINT,
    valuation_ts         TIMESTAMPTZ,

    raw_payload_json     JSONB,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_aum_row_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_aum_row_snapshot FOREIGN KEY (id_org, id_aum_snapshot)
        REFERENCES aum_snapshots(id_org, id_aum_snapshot)
        ON DELETE CASCADE,
    CONSTRAINT fk_aum_row_snapshot_match FOREIGN KEY (id_org, id_aum_snapshot, id_f, as_of_date)
        REFERENCES aum_snapshots(id_org, id_aum_snapshot, id_f, as_of_date),
    CONSTRAINT fk_aum_row_fund FOREIGN KEY (id_org, id_f) REFERENCES funds(id_org, id_f),
    CONSTRAINT fk_aum_row_ccy FOREIGN KEY (id_ccy) REFERENCES currencies(id_ccy),

    UNIQUE (uuid),
    UNIQUE (id_org, id_aum_snapshot)
);

CREATE INDEX IF NOT EXISTS idx_aum_rows_org ON aum_rows(id_org);
CREATE INDEX IF NOT EXISTS idx_aum_rows_snapshot ON aum_rows(id_org, id_aum_snapshot);
CREATE INDEX IF NOT EXISTS idx_aum_rows_fund ON aum_rows(id_org, id_f);
CREATE INDEX IF NOT EXISTS idx_aum_rows_as_of_date ON aum_rows(id_org, as_of_date);
