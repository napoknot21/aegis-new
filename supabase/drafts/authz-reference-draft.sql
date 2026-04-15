-- ============================================================
-- AEGIS - authz and reference foundation draft
-- Scope:
--   - organisations
--   - offices
--   - departments
--   - office_departments
--   - users sourced from Microsoft Entra / MSAL
--   - ranks
--   - access roles
--   - user assignments
--
-- Notes:
--   - This draft uses `users` as requested for the application table.
--   - `entra_oid` is the canonical identity key from Microsoft Entra ID.
--   - Authentication happens outside the database; this schema models
--     application users and authorization data.
--   - Tenant boundary = organisation.
--   - Join tables carry `id_org` explicitly to prevent cross-tenant links.
--   - RLS and grants must be added in a later migration.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- ORGANISATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS organisations (

    id_org          BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    code            TEXT        NOT NULL,
    legal_name      TEXT        NOT NULL,
    display_name    TEXT,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (uuid),
    UNIQUE (code)

);


-- ============================================================
-- OFFICES
-- ============================================================

CREATE TABLE IF NOT EXISTS offices (

    id_off          BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org          BIGINT      NOT NULL,

    code            TEXT        NOT NULL,
    name            TEXT        NOT NULL,
    city            TEXT,
    country_code    TEXT,
    timezone_name   TEXT,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_office_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_off),
    UNIQUE (id_org, code),
    UNIQUE (id_org, name)

);

CREATE INDEX IF NOT EXISTS idx_offices_org ON offices(id_org);


-- ============================================================
-- DEPARTMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS departments (

    id_dep          BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org          BIGINT      NOT NULL,

    code            TEXT        NOT NULL,
    name            TEXT        NOT NULL,
    description     TEXT,

    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_department_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_dep),
    UNIQUE (id_org, code),
    UNIQUE (id_org, name)

);

CREATE INDEX IF NOT EXISTS idx_departments_org ON departments(id_org);


-- ============================================================
-- OFFICE <-> DEPARTMENT
-- Which departments are present in which office
-- ============================================================

CREATE TABLE IF NOT EXISTS office_departments (

    id_off_dep      BIGSERIAL   PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org          BIGINT      NOT NULL,
    id_off          BIGINT      NOT NULL,
    id_dep          BIGINT      NOT NULL,

    is_primary      BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_off_dep_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_off_dep_office FOREIGN KEY (id_org, id_off) REFERENCES offices(id_org, id_off),
    CONSTRAINT fk_off_dep_department FOREIGN KEY (id_org, id_dep) REFERENCES departments(id_org, id_dep),

    UNIQUE (uuid),
    UNIQUE (id_org, id_off_dep),
    UNIQUE (id_org, id_off, id_dep)

);

CREATE INDEX IF NOT EXISTS idx_office_departments_org ON office_departments(id_org);
CREATE INDEX IF NOT EXISTS idx_office_departments_office ON office_departments(id_off);
CREATE INDEX IF NOT EXISTS idx_office_departments_department ON office_departments(id_dep);


-- ============================================================
-- USERS
-- Application users mapped from Microsoft Entra / MSAL
-- ============================================================

CREATE TABLE IF NOT EXISTS users (

    id_user          BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,

    entra_oid        UUID        NOT NULL,
    email            TEXT        NOT NULL,
    display_name     TEXT        NOT NULL,
    given_name       TEXT,
    family_name      TEXT,
    job_title        TEXT,

    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    last_login_at    TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_user),
    UNIQUE (id_org, entra_oid),
    UNIQUE (id_org, email)

);

CREATE INDEX IF NOT EXISTS idx_users_entra_oid ON users(entra_oid);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(id_org);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ============================================================
-- USER <-> OFFICE
-- A user may belong to one or more offices
-- ============================================================

CREATE TABLE IF NOT EXISTS user_offices (

    id_user_off      BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_user          BIGINT      NOT NULL,
    id_off           BIGINT      NOT NULL,

    is_primary       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_off_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_user_off_user FOREIGN KEY (id_org, id_user) REFERENCES users(id_org, id_user),
    CONSTRAINT fk_user_off_office FOREIGN KEY (id_org, id_off) REFERENCES offices(id_org, id_off),

    UNIQUE (uuid),
    UNIQUE (id_org, id_user, id_off)

);

CREATE INDEX IF NOT EXISTS idx_user_offices_org ON user_offices(id_org);
CREATE INDEX IF NOT EXISTS idx_user_offices_user ON user_offices(id_user);
CREATE INDEX IF NOT EXISTS idx_user_offices_office ON user_offices(id_off);


-- ============================================================
-- USER <-> OFFICE_DEPARTMENT
-- This ensures departments assigned to users exist in the office
-- ============================================================

CREATE TABLE IF NOT EXISTS user_departments (

    id_user_dep      BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_user          BIGINT      NOT NULL,
    id_off_dep       BIGINT      NOT NULL,

    is_primary       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_dep_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_user_dep_user FOREIGN KEY (id_org, id_user) REFERENCES users(id_org, id_user),
    CONSTRAINT fk_user_dep_off_dep FOREIGN KEY (id_org, id_off_dep) REFERENCES office_departments(id_org, id_off_dep),

    UNIQUE (uuid),
    UNIQUE (id_org, id_user, id_off_dep)

);

CREATE INDEX IF NOT EXISTS idx_user_departments_org ON user_departments(id_org);
CREATE INDEX IF NOT EXISTS idx_user_departments_user ON user_departments(id_user);
CREATE INDEX IF NOT EXISTS idx_user_departments_off_dep ON user_departments(id_off_dep);


-- ============================================================
-- RANKS
-- Hierarchical titles like board, head_of, intern, etc.
-- ============================================================

CREATE TABLE IF NOT EXISTS ranks (

    id_rank          BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,

    code             TEXT        NOT NULL,
    name             TEXT        NOT NULL,
    rank_level       INTEGER     NOT NULL,
    description      TEXT,

    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_rank_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_rank),
    UNIQUE (id_org, code),
    UNIQUE (id_org, rank_level)

);

CREATE INDEX IF NOT EXISTS idx_ranks_org ON ranks(id_org);


-- ============================================================
-- USER <-> RANK
-- Keep this separate in case rank history matters later
-- ============================================================

CREATE TABLE IF NOT EXISTS user_ranks (

    id_user_rank     BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_user          BIGINT      NOT NULL,
    id_rank          BIGINT      NOT NULL,

    is_primary       BOOLEAN     NOT NULL DEFAULT TRUE,
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    assigned_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_rank_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_user_rank_user FOREIGN KEY (id_org, id_user) REFERENCES users(id_org, id_user),
    CONSTRAINT fk_user_rank_rank FOREIGN KEY (id_org, id_rank) REFERENCES ranks(id_org, id_rank),

    UNIQUE (uuid),
    UNIQUE (id_org, id_user, id_rank)

);

CREATE INDEX IF NOT EXISTS idx_user_ranks_org ON user_ranks(id_org);
CREATE INDEX IF NOT EXISTS idx_user_ranks_user ON user_ranks(id_user);
CREATE INDEX IF NOT EXISTS idx_user_ranks_rank ON user_ranks(id_rank);


-- ============================================================
-- ACCESS ROLES
-- These are app permissions, not hierarchy titles
-- Examples:
--   - super_admin
--   - board_read
--   - risk_write
--   - trade_booker
--   - tech_admin
-- ============================================================

CREATE TABLE IF NOT EXISTS access_roles (

    id_role          BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,

    code             TEXT        NOT NULL,
    name             TEXT        NOT NULL,
    description      TEXT,

    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_access_role_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),

    UNIQUE (uuid),
    UNIQUE (id_org, id_role),
    UNIQUE (id_org, code)

);

CREATE INDEX IF NOT EXISTS idx_access_roles_org ON access_roles(id_org);


-- ============================================================
-- USER <-> ACCESS ROLE
-- Fine-grained permissions can be added later on top of this
-- ============================================================

CREATE TABLE IF NOT EXISTS user_access_roles (

    id_user_role     BIGSERIAL   PRIMARY KEY,
    uuid             UUID        NOT NULL DEFAULT uuid_generate_v4(),

    id_org           BIGINT      NOT NULL,
    id_user          BIGINT      NOT NULL,
    id_role          BIGINT      NOT NULL,

    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    assigned_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_role_org FOREIGN KEY (id_org) REFERENCES organisations(id_org),
    CONSTRAINT fk_user_role_user FOREIGN KEY (id_org, id_user) REFERENCES users(id_org, id_user),
    CONSTRAINT fk_user_role_role FOREIGN KEY (id_org, id_role) REFERENCES access_roles(id_org, id_role),

    UNIQUE (uuid),
    UNIQUE (id_org, id_user, id_role)

);

CREATE INDEX IF NOT EXISTS idx_user_access_roles_org ON user_access_roles(id_org);
CREATE INDEX IF NOT EXISTS idx_user_access_roles_user ON user_access_roles(id_user);
CREATE INDEX IF NOT EXISTS idx_user_access_roles_role ON user_access_roles(id_role);
