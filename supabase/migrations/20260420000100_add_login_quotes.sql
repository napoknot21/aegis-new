-- ============================================================
-- AEGIS - official migration: login quotes system reference
--
-- Scope:
--   - quotes (for login page display)
--
-- Notes:
--   - These quotes are displayed on the login page
--   - Not tenant-scoped, shared across all users
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- QUOTES
-- ============================================================

CREATE TABLE IF NOT EXISTS quotes (

    id_quote        BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    quote           TEXT        NOT NULL,
    author          TEXT        NOT NULL,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order      INTEGER     NOT NULL DEFAULT 100,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (uuid),
    UNIQUE (quote, author)

);

CREATE INDEX IF NOT EXISTS idx_quotes_active ON quotes(is_active);
CREATE INDEX IF NOT EXISTS idx_quotes_sort_order ON quotes(sort_order);


-- ============================================================
-- SEED INITIAL QUOTES
-- ============================================================

INSERT INTO quotes (quote, author, sort_order) VALUES
    ('Discipline is choosing between what you want now and what you want most.', 'Abraham Lincoln', 10),
    ('Risk comes from not knowing what you''re doing.', 'Warren Buffett', 20),
    ('The first rule is not to lose. The second rule is not to forget the first rule.', 'Warren Buffett', 30),
    ('In investing, what is comfortable is rarely profitable.', 'Robert Arnott', 40)
ON CONFLICT (quote, author) DO NOTHING;
