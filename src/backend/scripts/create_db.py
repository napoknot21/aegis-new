#!/usr/bin/env python3
"""
create_db.py  ·  Aegis — Complete Database Schema v6
──────────────────────────────────────────────────────
Run once per environment:
    python create_db.py --db-path aegis.db
    python create_db.py --db-path /data/aegis.db

Safe to re-run — CREATE TABLE IF NOT EXISTS / INSERT OR IGNORE everywhere.

══════════════════════════════════════════════════════════════════════
IDENTITY & ACCESS MODEL
══════════════════════════════════════════════════════════════════════

  The access model has 5 orthogonal dimensions:

  1. ORGANISATION   Who do you belong to?   (Heroics, ClientXYZ…)
  2. OFFICE         Where are you based?    (Luxembourg, Monaco)
                    Provider-side concept only. Clients have no offices.
  3. DEPARTMENT     What is your function?  (PM, RM, Compliance…)
                    Global catalogue, reusable by any org/client.
  4. POSITION       What is your rank?      (intern → head_of → admin)
                    Global catalogue. Combined with department = effective role.
  5. FUND ACCESS    Which funds can you touch?
                    Provider users: position-gated + explicit assignment
                    Client users:   their own org's funds only

  Effective role = (department, position) combination
  → drives which permissions you have
  → drives which pages you see
  → drives what actions you can take (buttons, forms, exports)

──────────────────────────────────────────────────────────────────────
HEROICS CAPITAL (provider) structure:

  LUXEMBOURG  (discretionary management)
    PM          — intern, analyst, officer/trader_quant, senior, deputy, head_of
    RM          — intern, analyst, officer, senior, deputy, head_of
    Research    — intern, analyst, officer, senior, head_of
    Technology  — intern, developer, senior_dev, head_of
    Compliance  — intern, analyst, officer, senior, head_of
    Board       — board_member, board_director
    Admin       — any position. ALL positions in Admin get ALL permissions.
                  intern in Admin = full admin. Intentional by design.

  MONACO  (advisory)
    Compliance  — intern, analyst, officer, senior, head_of
    Sales       — intern, analyst, officer, senior, head_of
    Advisory    — intern, analyst, officer, senior, head_of
    Board       — board_member, board_director
    Admin       — any position (same union rule)

──────────────────────────────────────────────────────────────────────
ADMIN MODEL:

  Admin is a DEPARTMENT. Any position within it → ALL permissions.

  Provider Admin  org=Heroics, dept=Admin
    → all orgs, all client funds (automatic, no grant needed)

  Client Admin    org=ClientXYZ, dept=Admin
    → scoped to their org only (enforced application-side)
    → never sees Heroics internals or other clients

  Board / DG      dept=Board, pos=board_member or board_director
    → read + export + escalate only. NO write/run/edit.
    → Does NOT validate breaches (CSSF segregation of duties)

──────────────────────────────────────────────────────────────────────
CLIENT-FUND ACCESS RULES (provider side):

  An Heroics user can access a client fund if ALL conditions are met:
    1. position.seniority_rank >= 3  (officer minimum — never intern/analyst)
    2. department allows client access  (PM, RM, Compliance, Advisory, Board)
       Technology → only if position = head_of
    3. Explicit assignment exists in user_fund_access table
       (even Head of RM needs an explicit entry per client fund)

  Exception: Provider Admin → automatic access to all client funds

──────────────────────────────────────────────────────────────────────
OFFICE CLOISONNEMENT (CSSF requirement):

  A user sees only data from their office UNLESS:
    - department.can_cross_offices = 1  (Board, Admin, Compliance)
    - They have an explicit cross-office assignment

══════════════════════════════════════════════════════════════════════
PERMISSIONS MODEL
══════════════════════════════════════════════════════════════════════

  Permissions are ATOMIC ACTIONS, not roles:
    "page.leverage.view"          "page.breach.validate"
    "page.nav.export"             "analysis.breach.run"
    "table.leverage.edit"         "user.create"
    "breach.comment.rm"           "breach.comment.pm"
    "fund.config.edit"            "report.export"

  Permission resolution:
    1. Find user's (department, position) combination
    2. Look up dept_position_permissions for that combo
    3. Merge with any direct user_permissions overrides
    4. Check fund-scope: does this permission apply to this fund?

  This replaces the old (can_view, can_export, can_validate_breach, can_run_analysis)
  columns — those were too coarse.

══════════════════════════════════════════════════════════════════════
TABLES
══════════════════════════════════════════════════════════════════════

  IAM Core
    organisations           tenant (provider + clients)
    offices                 Lux / Monaco (provider only)
    departments             global catalogue (PM, RM, Compliance…)
    positions               global catalogue with seniority_rank
    dept_office_map         which departments exist in which offices
    users                   + office_id, department_id, position_id
    user_fund_access        explicit fund assignment with access_level
                            required for provider users on client funds

  Permissions
    permissions             atomic action catalogue
    dept_position_perms     (dept, position) → [permission, …]
    user_permission_overrides  direct overrides for specific users
    sections                nav sections (Risk / Portfolio / Compliance…)
    pages                   all views, linked to a section
    page_required_perms     which permissions unlock a page

  Funds & Paths
    funds                   (org_id, name, slug, currency)
    fund_data_paths         (fund_id, data_type, path)

  Controls
    control_definitions     code (L01…), category, org_id
    control_zones           N zones, is_symmetric
    control_metrics         which columns feed each control

  Breach Workflow
    control_breaches        fund_id scoped
    breach_comments         user_id + position_id FKs

  Domain Data
    nav_history, nav_portfolio, nav_estimate
    subred_aum, subred_raw

  Misc
    chat_messages, audit_log
"""

import os, sys, json, sqlite3, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ════════════════════════════════════════════════════════════════════
# DDL
# ════════════════════════════════════════════════════════════════════

DDL_STATEMENTS = [

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  ORGANISATIONS                                               ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS organisations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT    NOT NULL,           -- "Heroics Capital"
        slug            TEXT    NOT NULL UNIQUE,    -- "heroics"
        is_provider     INTEGER NOT NULL DEFAULT 0, -- 1 = software vendor
        country         TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  OFFICES  (provider only — clients have no offices)          ║
    # ║                                                              ║
    # ║  Represents physical locations of the provider.             ║
    # ║  Drives the Lux/Monaco cloisonnement rule.                  ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS offices (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id          INTEGER NOT NULL REFERENCES organisations(id),
        name            TEXT    NOT NULL,           -- "Luxembourg"
        city            TEXT    NOT NULL,           -- "Luxembourg City"
        country_code    TEXT    NOT NULL,           -- "LU"
        office_type     TEXT    NOT NULL,           -- "discretionary" | "advisory"
        is_active       INTEGER NOT NULL DEFAULT 1,
        UNIQUE (org_id, name)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_offices_org ON offices (org_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  DEPARTMENTS                                                  ║
    # ║                                                              ║
    # ║  Global catalogue — reusable by provider AND clients.       ║
    # ║  A client can use "PM", "RM", "Compliance" for their         ║
    # ║  own internal structure without any code change.             ║
    # ║                                                              ║
    # ║  can_access_client_funds:                                   ║
    # ║    1 → department CAN access client funds (subject to       ║
    # ║        position.seniority_rank >= 3 AND explicit assignment) ║
    # ║    0 → never, regardless of position                        ║
    # ║                                                              ║
    # ║  can_cross_offices:                                          ║
    # ║    1 → Board, Admin, Compliance can see both Lux + Monaco   ║
    # ║    0 → cloisonné to their own office                        ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS departments (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        name                    TEXT    NOT NULL UNIQUE,  -- "PM", "RM", "Compliance"…
        display_name            TEXT    NOT NULL,
        can_access_client_funds INTEGER NOT NULL DEFAULT 0,
        can_cross_offices       INTEGER NOT NULL DEFAULT 0,
        description             TEXT
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  POSITIONS                                                    ║
    # ║                                                              ║
    # ║  Global catalogue of seniority levels.                      ║
    # ║  seniority_rank drives the client fund access gate:         ║
    # ║    rank < 3  → never access client funds (intern, analyst)  ║
    # ║    rank >= 3 → eligible IF dept.can_access_client_funds=1   ║
    # ║               AND explicit assignment in user_fund_access   ║
    # ║                                                              ║
    # ║  display_name is org-configurable (e.g. "Trader Quant"      ║
    # ║  instead of "officer" for the PM department).               ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS positions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT    NOT NULL UNIQUE,  -- canonical code
        display_name    TEXT    NOT NULL,
        seniority_rank  INTEGER NOT NULL,
        -- 1=intern  2=analyst  3=officer  4=senior  5=deputy  6=head_of
        -- 7=board   8=admin
        description     TEXT
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  DEPT-OFFICE MAP                                             ║
    # ║                                                              ║
    # ║  Which departments exist in which offices (provider side).  ║
    # ║  Enforces: Sales and Advisory are Monaco-only.              ║
    # ║            PM and RM are Lux-only.                          ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS dept_office_map (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id   INTEGER NOT NULL REFERENCES departments(id),
        office_id       INTEGER NOT NULL REFERENCES offices(id),
        UNIQUE (department_id, office_id)
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  DEPT-POSITION MAP                                           ║
    # ║                                                              ║
    # ║  Which positions are valid within a given department.        ║
    # ║  Also carries the org-specific display_name override:       ║
    # ║    PM dept + officer position → display "Trader Quant"      ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS dept_position_map (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id       INTEGER NOT NULL REFERENCES departments(id),
        position_id         INTEGER NOT NULL REFERENCES positions(id),
        display_name_override TEXT,   -- "Trader Quant" overrides "Officer"
        UNIQUE (department_id, position_id)
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  USERS                                                        ║
    # ║                                                              ║
    # ║  One row per person. org_id = primary/home org.             ║
    # ║  office_id = their physical location (NULL for clients).    ║
    # ║  department_id + position_id = their role at their home org.║
    # ║                                                              ║
    # ║  Auth flow:                                                  ║
    # ║    1. SELECT * FROM users WHERE email=? AND is_active=1     ║
    # ║    2. Resolve effective permissions via                      ║
    # ║       dept_position_perms + user_permission_overrides        ║
    # ║    3. Check user_fund_access for fund-scoped access         ║
    # ║    4. Build allowed sections/pages/actions for the session  ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id          INTEGER NOT NULL REFERENCES organisations(id),
        office_id       INTEGER          REFERENCES offices(id),
        -- NULL for client users (they have no office concept)
        department_id   INTEGER          REFERENCES departments(id),
        position_id     INTEGER          REFERENCES positions(id),
        first_name      TEXT    NOT NULL,
        last_name       TEXT    NOT NULL,
        username        TEXT    NOT NULL UNIQUE,
        email           TEXT    NOT NULL UNIQUE,
        hashed_password TEXT    NOT NULL,
        is_active       INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        last_login      TEXT,
        created_by      INTEGER          REFERENCES users(id)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_users_org        ON users (org_id)",
    "CREATE INDEX IF NOT EXISTS idx_users_email      ON users (email)",
    "CREATE INDEX IF NOT EXISTS idx_users_dept_pos   ON users (department_id, position_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  USER FUND ACCESS                                            ║
    # ║                                                              ║
    # ║  Explicit fund assignment. Required for provider users to   ║
    # ║  access client funds — even Head of RM needs an entry here. ║
    # ║                                                              ║
    # ║  access_level:                                              ║
    # ║    read       → can view all pages for this fund            ║
    # ║    read_write → can also validate breaches, run analysis    ║
    # ║    admin      → full control (only for Provider Admin)      ║
    # ║                                                              ║
    # ║  Client users do NOT need entries here for their own funds  ║
    # ║  — org membership is sufficient.                            ║
    # ║                                                              ║
    # ║  Provider admin users do NOT need entries here either       ║
    # ║  — their position gives automatic access.                   ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS user_fund_access (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
        fund_id         INTEGER NOT NULL REFERENCES funds(id),
        access_level    TEXT    NOT NULL DEFAULT 'read',
        -- read | read_write | admin
        granted_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        granted_by      INTEGER NOT NULL REFERENCES users(id),
        expires_at      TEXT,   -- NULL = permanent
        notes           TEXT,   -- reason for access / CSSF justification
        UNIQUE (user_id, fund_id)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_ufa_user ON user_fund_access (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_ufa_fund ON user_fund_access (fund_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  FUNDS                                                        ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS funds (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id          INTEGER NOT NULL REFERENCES organisations(id),
        name            TEXT    NOT NULL,
        slug            TEXT    NOT NULL,           -- "HV", "WR"
        currency        TEXT    NOT NULL DEFAULT 'EUR',
        inception_date  TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1,
        UNIQUE (org_id, slug)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_funds_org ON funds (org_id)",

    """
    CREATE TABLE IF NOT EXISTS fund_data_paths (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id     INTEGER NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
        data_type   TEXT    NOT NULL,
        -- "NAV" | "NAV_Estimate" | "Leverage" | "Leverage_Per_Trade" | "SIMM" …
        path        TEXT    NOT NULL,
        UNIQUE (fund_id, data_type)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_fund_paths_fund ON fund_data_paths (fund_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  PERMISSIONS — atomic action catalogue                       ║
    # ║                                                              ║
    # ║  Each permission is one specific thing you can do.          ║
    # ║  Format: "domain.resource.action"                           ║
    # ║                                                              ║
    # ║  Examples:                                                   ║
    # ║    page.leverage.view           page.nav.export             ║
    # ║    page.breach.view             page.breach.validate        ║
    # ║    analysis.breach.run          analysis.nav.refresh        ║
    # ║    table.leverage.edit          table.nav.comment           ║
    # ║    breach.comment.rm            breach.comment.pm           ║
    # ║    fund.config.edit             fund.data_path.edit         ║
    # ║    user.create                  user.deactivate             ║
    # ║    user.fund_access.grant       org.config.edit             ║
    # ║    report.cssf.export           report.risk.export          ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS permissions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT    NOT NULL UNIQUE,    -- "page.breach.validate"
        domain      TEXT    NOT NULL,           -- "page" | "analysis" | "table" | "breach" | "fund" | "user" | "report"
        resource    TEXT    NOT NULL,           -- "leverage" | "breach" | "nav"…
        action      TEXT    NOT NULL,           -- "view" | "export" | "edit" | "validate" | "run"…
        description TEXT
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_permissions_domain ON permissions (domain)",
    "CREATE INDEX IF NOT EXISTS idx_permissions_code   ON permissions (code)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  DEPT-POSITION PERMISSIONS                                   ║
    # ║                                                              ║
    # ║  The combination (department, position) → set of            ║
    # ║  permissions. This is the core of the RBAC model.           ║
    # ║                                                              ║
    # ║  org_id = NULL → global default (applies to all orgs)       ║
    # ║  org_id = X    → override for org X only                    ║
    # ║                                                              ║
    # ║  Example rows:                                               ║
    # ║    dept=RM, pos=officer  → page.leverage.view               ║
    # ║    dept=RM, pos=officer  → page.breach.view                 ║
    # ║    dept=RM, pos=officer  → breach.comment.rm                ║
    # ║    dept=RM, pos=head_of  → analysis.breach.run              ║
    # ║    dept=PM, pos=officer  → page.leverage.view               ║
    # ║    dept=Admin, pos=admin → user.create  (all resources)     ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS dept_position_perms (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id   INTEGER NOT NULL REFERENCES departments(id),
        position_id     INTEGER NOT NULL REFERENCES positions(id),
        permission_id   INTEGER NOT NULL REFERENCES permissions(id),
        org_id          INTEGER          REFERENCES organisations(id),
        -- NULL = global default, SET = org-specific override
        UNIQUE (department_id, position_id, permission_id, org_id)
    )
    """,

    "CREATE UNIQUE INDEX IF NOT EXISTS uidx_dpp_global ON dept_position_perms (department_id, position_id, permission_id) WHERE org_id IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_dpp_dept_pos ON dept_position_perms (department_id, position_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  USER PERMISSION OVERRIDES                                   ║
    # ║                                                              ║
    # ║  Direct per-user overrides — GRANT or REVOKE.               ║
    # ║  Use sparingly. Prefer fixing (dept, position) permissions. ║
    # ║                                                              ║
    # ║  grant_or_revoke:                                            ║
    # ║    'grant'  → user gets this permission even if their       ║
    # ║               (dept, pos) combo doesn't have it             ║
    # ║    'revoke' → user loses this permission even if their      ║
    # ║               (dept, pos) combo has it                      ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS user_permission_overrides (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        permission_id   INTEGER NOT NULL REFERENCES permissions(id),
        grant_or_revoke TEXT    NOT NULL CHECK (grant_or_revoke IN ('grant','revoke')),
        fund_id         INTEGER          REFERENCES funds(id),
        -- NULL = applies to all funds; SET = only for this fund
        granted_by      INTEGER NOT NULL REFERENCES users(id),
        reason          TEXT,
        granted_at      TEXT    NOT NULL DEFAULT (datetime('now')),
        expires_at      TEXT,   -- NULL = permanent
        UNIQUE (user_id, permission_id, fund_id)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_upo_user ON user_permission_overrides (user_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  SECTIONS  (navigation groups)                               ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS sections (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        slug            TEXT    NOT NULL UNIQUE,    -- "risk", "portfolio"…
        display_name    TEXT    NOT NULL,
        icon            TEXT,                       -- emoji or icon code
        sort_order      INTEGER NOT NULL DEFAULT 0,
        is_active       INTEGER NOT NULL DEFAULT 1
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  PAGES  (individual views / tabs)                            ║
    # ║                                                              ║
    # ║  slug matches your Excel folder names exactly.              ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS pages (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id      INTEGER NOT NULL REFERENCES sections(id),
        slug            TEXT    NOT NULL UNIQUE,
        display_name    TEXT    NOT NULL,
        sort_order      INTEGER NOT NULL DEFAULT 0,
        is_active       INTEGER NOT NULL DEFAULT 1,
        description     TEXT
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_pages_section ON pages (section_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  PAGE REQUIRED PERMISSIONS                                   ║
    # ║                                                              ║
    # ║  A page is accessible if the user has AT LEAST ONE of       ║
    # ║  its required permissions (OR logic).                       ║
    # ║  For stricter pages, list multiple AND they all need to     ║
    # ║  be present (use is_required=1 for AND logic).              ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS page_required_perms (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id         INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
        permission_id   INTEGER NOT NULL REFERENCES permissions(id),
        is_required     INTEGER NOT NULL DEFAULT 0,
        -- 0 = OR (any of these unlocks the page)
        -- 1 = AND (all required=1 perms must be present)
        UNIQUE (page_id, permission_id)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_prp_page ON page_required_perms (page_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  CONTROLS                                                    ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS control_definitions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT    NOT NULL,
        name        TEXT    NOT NULL,
        category    TEXT    NOT NULL,
        tab_label   TEXT,
        description TEXT,
        org_id      INTEGER REFERENCES organisations(id),
        UNIQUE (code, org_id)
    )
    """,

    "CREATE UNIQUE INDEX IF NOT EXISTS uidx_ctrl_def_global ON control_definitions (code) WHERE org_id IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_ctrl_def_code ON control_definitions (code)",
    "CREATE INDEX IF NOT EXISTS idx_ctrl_def_cat  ON control_definitions (category)",

    """
    CREATE TABLE IF NOT EXISTS control_zones (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        control_id          INTEGER NOT NULL REFERENCES control_definitions(id) ON DELETE CASCADE,
        zone_order          INTEGER NOT NULL,
        label               TEXT    NOT NULL,
        color_rgba          TEXT    NOT NULL,
        is_symmetric        INTEGER NOT NULL DEFAULT 0,
        lower_bound         REAL,
        lower_inclusive     INTEGER NOT NULL DEFAULT 0,
        upper_bound         REAL,
        upper_inclusive     INTEGER NOT NULL DEFAULT 1,
        action_description  TEXT    NOT NULL,
        notify_roles        TEXT,
        cssf_notify_hours   INTEGER,
        UNIQUE (control_id, zone_order)
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_ctrl_zones_ctrl ON control_zones (control_id)",

    """
    CREATE TABLE IF NOT EXISTS control_metrics (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        control_id      INTEGER NOT NULL REFERENCES control_definitions(id) ON DELETE CASCADE,
        metric_name     TEXT    NOT NULL,
        column_source   TEXT,
        unit            TEXT,
        is_absolute     INTEGER NOT NULL DEFAULT 0
    )
    """,

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  BREACH WORKFLOW                                             ║
    # ║                                                              ║
    # ║  Status lifecycle:                                          ║
    # ║    open          Detected by breach runner, no action yet   ║
    # ║    under_review  At least 1 RM comment posted               ║
    # ║    resolved      RM has closed the breach with justif.      ║
    # ║    escalated     RM escalated to management (serious cases) ║
    # ║    cssf_notified CSSF formally notified (48h zones)         ║
    # ║    reopened      Admin reopened a resolved breach           ║
    # ║                                                              ║
    # ║  Resolution rules (enforced app-side):                      ║
    # ║    - ≥ 1 RM comment always required before resolving        ║
    # ║    - PM comment optional (their choice, not mandatory)      ║
    # ║    - Only RM with rank ≥ 5 (deputy/head_of) can resolve     ║
    # ║    - PM of SAME ORG as fund can comment (rank ≥ 3)         ║
    # ║    - RM of SAME ORG can comment (rank ≥ 3)                 ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS control_breaches (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id          INTEGER NOT NULL REFERENCES organisations(id),
        fund_id         INTEGER NOT NULL REFERENCES funds(id),
        control_id      INTEGER NOT NULL REFERENCES control_definitions(id),
        zone_id         INTEGER          REFERENCES control_zones(id),
        metric_name     TEXT,
        run_date        TEXT    NOT NULL,    -- "2025/07/03 (09h23)"
        breach_value    TEXT    NOT NULL,    -- "311.24%"
        breach_level    TEXT    NOT NULL,    -- "300%" — threshold crossed
        status          TEXT    NOT NULL DEFAULT 'open'
                        CHECK (status IN (
                            'open',
                            'under_review',
                            'resolved',
                            'escalated',
                            'cssf_notified',
                            'reopened'
                        )),
        resolved_by     INTEGER          REFERENCES users(id),
        resolved_at     TEXT,
        cssf_deadline   TEXT,   -- datetime('now', '+48 hours') if cssf_notify_hours set
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_breaches_org_fund  ON control_breaches (org_id, fund_id)",
    "CREATE INDEX IF NOT EXISTS idx_breaches_run_date  ON control_breaches (run_date)",
    "CREATE INDEX IF NOT EXISTS idx_breaches_ctrl      ON control_breaches (control_id)",
    "CREATE INDEX IF NOT EXISTS idx_breaches_status    ON control_breaches (status)",
    "CREATE INDEX IF NOT EXISTS idx_breaches_deadline  ON control_breaches (cssf_deadline) WHERE cssf_deadline IS NOT NULL",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  BREACH COMMENTS                                             ║
    # ║                                                              ║
    # ║  Who can comment:                                           ║
    # ║    RM: dept=RM, rank >= 3 (officer+), same org as fund      ║
    # ║    PM: dept=PM, rank >= 3 (officer+), same org as fund      ║
    # ║    No restriction on number of comments per user            ║
    # ║    department_id + position_id = snapshot at time of post   ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS breach_comments (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        breach_id       INTEGER NOT NULL REFERENCES control_breaches(id) ON DELETE CASCADE,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        department_id   INTEGER NOT NULL REFERENCES departments(id),
        position_id     INTEGER NOT NULL REFERENCES positions(id),
        -- Snapshot: captures dept+pos AT THE TIME of commenting.
        -- If user changes role later, history remains coherent.
        comment         TEXT    NOT NULL,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_bc_breach ON breach_comments (breach_id)",
    "CREATE INDEX IF NOT EXISTS idx_bc_user   ON breach_comments (user_id, department_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  BREACH ATTACHMENTS                                          ║
    # ║                                                              ║
    # ║  Justification documents attached to breach comments.       ║
    # ║  Files stored on disk; path recorded here.                  ║
    # ║                                                              ║
    # ║  Physical storage:                                           ║
    # ║    N:\AEGIS\ATTACHMENTS\breaches\{breach_id}\               ║
    # ║      {timestamp}_{original_filename}                        ║
    # ║                                                              ║
    # ║  comment_id = NULL means attached to the breach itself      ║
    # ║  comment_id = X   means attached to a specific comment      ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS breach_attachments (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        breach_id       INTEGER NOT NULL REFERENCES control_breaches(id) ON DELETE CASCADE,
        comment_id      INTEGER          REFERENCES breach_comments(id)  ON DELETE SET NULL,
        uploaded_by     INTEGER NOT NULL REFERENCES users(id),
        original_name   TEXT    NOT NULL,   -- "justification_leverage_2025.pdf"
        stored_path     TEXT    NOT NULL,   -- full filesystem path
        mime_type       TEXT,               -- "application/pdf", "image/png"…
        file_size_bytes INTEGER,
        uploaded_at     TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_ba_breach  ON breach_attachments (breach_id)",
    "CREATE INDEX IF NOT EXISTS idx_ba_comment ON breach_attachments (comment_id)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  NAV DOMAIN                                                  ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS nav_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id         INTEGER NOT NULL REFERENCES funds(id),
        portfolio_name  TEXT    NOT NULL,
        mv              REAL,
        mv_nav_pct      REAL,
        comment         TEXT,
        date            TEXT    NOT NULL,
        UNIQUE (fund_id, portfolio_name, date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_nav_history_fund_date ON nav_history (fund_id, date)",

    """
    CREATE TABLE IF NOT EXISTS nav_portfolio (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id         INTEGER NOT NULL REFERENCES funds(id),
        date            TEXT    NOT NULL,
        portfolio_name  TEXT    NOT NULL,
        mv              REAL,
        mv_nav_pct      REAL,
        UNIQUE (fund_id, date, portfolio_name)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_nav_portfolio_fund_date ON nav_portfolio (fund_id, date)",

    """
    CREATE TABLE IF NOT EXISTS nav_estimate (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id              INTEGER NOT NULL REFERENCES funds(id),
        date                 TEXT    NOT NULL,
        gav                  REAL,
        weighted_performance REAL,
        UNIQUE (fund_id, date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_nav_estimate_fund_date ON nav_estimate (fund_id, date)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  SUBRED DOMAIN                                               ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS subred_aum (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id  INTEGER NOT NULL REFERENCES funds(id),
        date     TEXT    NOT NULL,
        amount   INTEGER,
        currency TEXT,
        UNIQUE (fund_id, date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_subred_aum_fund_date ON subred_aum (fund_id, date)",

    """
    CREATE TABLE IF NOT EXISTS subred_raw (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_id           INTEGER NOT NULL REFERENCES funds(id),
        date              TEXT    NOT NULL,
        trade_leg_code    TEXT,
        trade_description TEXT,
        trade_name        TEXT,
        book_name         TEXT,
        trade_type        TEXT,
        delivery_date     TEXT,
        notional          REAL,
        currency          TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_subred_raw_fund_date ON subred_raw (fund_id, date)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  CHAT                                                        ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        channel     TEXT    NOT NULL,
        org_id      INTEGER REFERENCES organisations(id),
        fund_id     INTEGER REFERENCES funds(id),
        user_id     INTEGER REFERENCES users(id),
        username    TEXT    NOT NULL,
        message     TEXT    NOT NULL,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_chat_channel ON chat_messages (channel, created_at)",

    # ╔══════════════════════════════════════════════════════════════╗
    # ║  AUDIT LOG                                                   ║
    # ╚══════════════════════════════════════════════════════════════╝
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          TEXT    NOT NULL DEFAULT (datetime('now')),
        org_id      INTEGER REFERENCES organisations(id),
        fund_id     INTEGER REFERENCES funds(id),
        user_id     INTEGER REFERENCES users(id),
        action      TEXT    NOT NULL,       -- "breach.comment.rm"
        resource    TEXT,                   -- "control_breaches:42"
        detail      TEXT                    -- JSON payload
    )
    """,
]


# ════════════════════════════════════════════════════════════════════
# SEED DATA
# ════════════════════════════════════════════════════════════════════

# ── Departments ──────────────────────────────────────────────────────
# (name, display_name, can_access_client_funds, can_cross_offices, description)
DEPARTMENT_SEED = [
    ("PM",          "Portfolio Management",  1, 0, "Manages fund portfolios. Lux only."),
    ("RM",          "Risk Management",       1, 0, "Risk monitoring and breach management. Lux only."),
    ("Research",    "Research",              1, 0, "Quantitative and fundamental research. Lux only."),
    ("Technology",  "Technology",            0, 0, "IT, dev, infrastructure. Lux only. No client fund access except Head of."),
    ("Compliance",  "Compliance",            1, 1, "Regulatory compliance. Lux + Monaco. Can cross offices."),
    ("Sales",       "Sales",                 0, 0, "Client acquisition and relations. Monaco only."),
    ("Advisory",    "Advisory",              1, 0, "Client advisory services. Monaco only."),
    ("Board",       "Board / Direction",     1, 1, "General direction. Read-only cross-office. Heroics + all clients."),
    ("Admin",       "Administration",        1, 1, "System admin. ALL positions in Admin get ALL permissions. Provider Admin = all orgs/funds. Client Admin = own org only."),
]

# ── Positions ─────────────────────────────────────────────────────────
# (name, display_name, seniority_rank, description)
POSITION_SEED = [
    ("intern",        "Intern / Stagiaire",      1, "Trainee. No client fund access. Limited pages."),
    ("analyst",       "Analyst",                 2, "Junior professional. No client fund access."),
    ("officer",       "Officer",                 3, "Qualified professional. Client fund access eligible."),
    ("senior",        "Senior",                  4, "Experienced professional. Client fund access eligible."),
    ("deputy",        "Deputy / Vice",           5, "Second-in-command. Client fund access eligible."),
    ("head_of",       "Head of Department",      6, "Department head. Full access within department scope."),
    ("board_member",  "Board Member",            7, "Non-executive board member. Read-only everywhere."),
    ("board_director","Board Director / DG",     7, "Executive director. Read-only + breach escalation."),
    ("admin",         "System Administrator",    8, "Full system access within org scope."),
]

# ── Sections ──────────────────────────────────────────────────────────
# (slug, display_name, icon, sort_order)
SECTION_SEED = [
    ("risk",          "Risk Monitoring",   "📊", 1),
    ("portfolio",     "Portfolio",         "💼", 2),
    ("compliance",    "Compliance",        "⚖️",  3),
    ("administration","Administration",    "⚙️",  4),
]

# ── Pages ─────────────────────────────────────────────────────────────
# (section_slug, slug, display_name, sort_order, description)
PAGE_SEED = [
    # Risk Monitoring
    ("risk", "leverage",                "Leverage — Fund Level",       1,  "Gross & Commitment Leverage (L01)"),
    ("risk", "leverage_per_trade",      "Leverage — Per Trade",        2,  "Exposure % NAV per position (L03)"),
    ("risk", "leverage_per_underlying", "Leverage — Per Underlying",   3,  "Delta/NAV% per underlying (L02)"),
    ("risk", "long_short_delta",        "Long / Short Delta",          4,  "Net long/short delta breakdown"),
    ("risk", "cross_delta",             "Cross Delta",                 5,  "Cross-asset delta exposure"),
    ("risk", "cross_gamma",             "Cross Gamma",                 6,  "Cross-asset gamma exposure"),
    ("risk", "vega_bucket",             "Vega Buckets",                7,  "Vega/NAV% by expiry bucket"),
    ("risk", "vega_stress_pnl",         "Vega Stress P&L",             8,  "Vega stress P&L scenarios"),
    ("risk", "delta_stress_pct",        "Delta Stress % NAV",          9,  "Delta stress as % of NAV"),
    ("risk", "delta_stress_abs",        "Delta Stress Abs",            10, "Delta stress in absolute terms"),
    ("risk", "delta_pnl_stress",        "Delta P&L Stress",            11, "Delta P&L stress scenarios"),
    ("risk", "gamma_pnl",               "Gamma P&L",                   12, "Gamma P&L exposure"),
    ("risk", "simm",                    "SIMM / VaR",                  13, "SIMM/NAV%, IM, VM (S01/S02/S03)"),
    ("risk", "overview_risks_equity_fx","Equity/FX Risk Overview",     14, "Equity and FX risk overview"),
    ("risk", "overview_risks_credit",   "Credit Risk Overview",        15, "Credit risk dashboard"),
    ("risk", "counterparty_concentration","Counterparty Concentration",16, "MV/NAV% per counterparty (CR01/CR02)"),
    ("risk", "plot_risk",               "P&L Plot Risk",               17, "Risk-based P&L chart"),
    ("risk", "expiries",                "Expiries",                    18, "Upcoming option/contract expiries"),

    # Portfolio
    ("portfolio", "nav",           "NAV History",    1, "Full NAV time series per fund"),
    ("portfolio", "nav_estimate",  "NAV Estimate",   2, "GAV and weighted performance estimate"),
    ("portfolio", "portfolio_view","Portfolio View",  3, "Per-book portfolio snapshot by date"),
    ("portfolio", "split_view",    "Split View",      4, "Side-by-side fund comparison"),

    # Compliance
    ("compliance", "breach_validation", "Breach Validation", 1, "CSSF breach workflow — RM/PM sign-off"),

    # Administration
    ("administration", "user_management",  "Users & Access",   1, "Manage users, departments, positions"),
    ("administration", "fund_config",      "Fund Configuration",2, "Manage funds, data paths, controls"),
    ("administration", "audit_log_view",   "Audit Log",        3, "Full system audit trail"),
    ("administration", "org_settings",     "Org Settings",     4, "Organisation configuration"),
]

# ── Permissions ───────────────────────────────────────────────────────
# (code, domain, resource, action, description)
PERMISSION_SEED = [
    # Page access
    ("page.risk.view",                 "page",     "risk",              "view",     "View all Risk pages"),
    ("page.portfolio.view",            "page",     "portfolio",         "view",     "View all Portfolio pages"),
    ("page.compliance.view",           "page",     "compliance",        "view",     "View Compliance section"),
    ("page.administration.view",       "page",     "administration",    "view",     "View Admin section"),

    # Page-level export
    ("page.risk.export",               "page",     "risk",              "export",   "Export risk data to Excel"),
    ("page.portfolio.export",          "page",     "portfolio",         "export",   "Export portfolio data to Excel"),
    ("page.compliance.export",         "page",     "compliance",        "export",   "Export compliance reports"),
    ("report.cssf.export",             "report",   "cssf",              "export",   "Export official CSSF breach report"),

    # Analysis / scripts
    ("analysis.breach.run",            "analysis", "breach",            "run",      "Run breach detection analysis"),
    ("analysis.nav.refresh",           "analysis", "nav",               "refresh",  "Trigger NAV data refresh from source"),
    ("analysis.simm.run",              "analysis", "simm",              "run",      "Run SIMM calculation"),

    # Breach workflow — RM specific
    ("breach.comment.rm",              "breach",   "comment",           "rm",       "Add RM-level breach comment"),
    ("breach.comment.pm",              "breach",   "comment",           "pm",       "Add PM-level breach comment"),
    ("breach.validate",                "breach",   "breach",            "validate", "Resolve or close a breach — RM only (rank >= deputy)"),
    ("breach.status.update",           "breach",   "status",            "update",   "Update breach status — RM only"),
    ("breach.escalate.board",          "breach",   "escalate",          "board",    "Board annotation: flag breach for DG attention (read annotation, no status change)"),

    # Table interactions
    ("table.breach.edit",              "table",    "breach",            "edit",     "Edit breach records"),
    ("table.leverage.comment",         "table",    "leverage",          "comment",  "Add comment on leverage table row"),
    ("table.nav.comment",              "table",    "nav",               "comment",  "Add comment on NAV table row"),

    # Fund management
    ("fund.config.view",               "fund",     "config",            "view",     "View fund configuration"),
    ("fund.config.edit",               "fund",     "config",            "edit",     "Edit fund name, currency, paths"),
    ("fund.data_path.edit",            "fund",     "data_path",         "edit",     "Edit fund data directory paths"),
    ("fund.access.grant",              "fund",     "access",            "grant",    "Grant another user access to a fund"),

    # User management
    ("user.view",                      "user",     "user",              "view",     "View user profiles"),
    ("user.create",                    "user",     "user",              "create",   "Create new users"),
    ("user.deactivate",                "user",     "user",              "deactivate","Deactivate a user account"),
    ("user.permission.override",       "user",     "permission",        "override", "Grant or revoke permissions for a specific user"),
    ("user.fund_access.grant",         "user",     "fund_access",       "grant",    "Assign a user to a client fund"),

    # Organisation / system
    ("org.config.view",                "org",      "config",            "view",     "View org configuration"),
    ("org.config.edit",                "org",      "config",            "edit",     "Edit org configuration"),
    ("org.create",                     "org",      "org",               "create",   "Create a new client org (provider admin only)"),

    # Client fund access
    ("client_fund.read",               "fund",     "client_fund",       "read",     "Read data from a client fund"),
    ("client_fund.write",              "fund",     "client_fund",       "write",    "Write/validate on a client fund"),
]


def _build_dept_position_perms():
    """
    Build the (department, position) → permissions mapping.

    Logic per department × position combination:
      All interns: page.risk.view + page.portfolio.view only
      Analysts: + exports on their domain
      Officers+: their domain's full permissions
      Head of: + run analysis, fund config view
      Admin: everything
      Board: page.*.view everywhere, NO write/edit/run
    """
    # (dept_name, pos_name, [permission_codes])
    matrix = []

    base_view = ["page.risk.view", "page.portfolio.view"]
    risk_export   = ["page.risk.export"]
    port_export   = ["page.portfolio.export"]
    compliance_view = ["page.compliance.view"]
    compliance_export = ["page.compliance.export", "report.cssf.export"]

    breach_rm_comment = ["breach.comment.rm"]
    breach_rm_validate= ["breach.validate", "breach.status.update"]  # deputy+ only
    breach_pm     = ["breach.comment.pm"]
    breach_run    = ["analysis.breach.run"]
    nav_refresh   = ["analysis.nav.refresh"]
    fund_cfg_view = ["fund.config.view"]
    fund_cfg_edit = ["fund.config.edit", "fund.data_path.edit", "fund.access.grant"]
    user_view     = ["user.view"]
    user_mgmt     = ["user.create", "user.deactivate", "user.permission.override", "user.fund_access.grant"]
    org_view      = ["org.config.view"]
    org_edit      = ["org.config.edit"]
    client_read   = ["client_fund.read"]
    client_write  = ["client_fund.write"]

    # ── PM ────────────────────────────────────────────────────────
    # PM can comment on breaches (officer+, same org) but NEVER validate
    matrix += [("PM", "intern",   base_view)]
    matrix += [("PM", "analyst",  base_view + risk_export + port_export)]
    matrix += [("PM", "officer",  base_view + risk_export + port_export + breach_pm + client_read)]
    matrix += [("PM", "senior",   base_view + risk_export + port_export + breach_pm + client_read + client_write)]
    matrix += [("PM", "deputy",   base_view + risk_export + port_export + breach_pm + breach_run + client_read + client_write + fund_cfg_view)]
    matrix += [("PM", "head_of",  base_view + risk_export + port_export + breach_pm + breach_run + client_read + client_write + fund_cfg_view + user_view)]

    # ── RM ────────────────────────────────────────────────────────
    # breach.validate ONLY for deputy and head_of (seniority_rank >= 5)
    matrix += [("RM", "intern",   base_view)]
    matrix += [("RM", "analyst",  base_view + risk_export)]
    matrix += [("RM", "officer",  base_view + risk_export + compliance_view + breach_rm_comment + client_read)]
    matrix += [("RM", "senior",   base_view + risk_export + compliance_view + breach_rm_comment + client_read + client_write)]
    matrix += [("RM", "deputy",   base_view + risk_export + compliance_view + breach_rm_comment + breach_rm_validate + breach_run + client_read + client_write + fund_cfg_view)]
    matrix += [("RM", "head_of",  base_view + risk_export + compliance_view + breach_rm_comment + breach_rm_validate + breach_run + client_read + client_write + fund_cfg_view + user_view)]

    # ── Research ─────────────────────────────────────────────────
    matrix += [("Research", "intern",  base_view)]
    matrix += [("Research", "analyst", base_view + risk_export + port_export)]
    matrix += [("Research", "officer", base_view + risk_export + port_export + client_read)]
    matrix += [("Research", "senior",  base_view + risk_export + port_export + client_read)]
    matrix += [("Research", "head_of", base_view + risk_export + port_export + client_read + fund_cfg_view + user_view)]

    # ── Technology ───────────────────────────────────────────────
    # No client fund access except head_of
    matrix += [("Technology", "intern",    base_view)]
    matrix += [("Technology", "analyst",   base_view)]  # dev analyst
    matrix += [("Technology", "officer",   base_view + risk_export + port_export + fund_cfg_view)]
    matrix += [("Technology", "senior",    base_view + risk_export + port_export + fund_cfg_view + fund_cfg_edit)]
    matrix += [("Technology", "head_of",   base_view + risk_export + port_export + fund_cfg_view + fund_cfg_edit
                                           + client_read + user_view + user_mgmt + org_view)]

    # ── Compliance ───────────────────────────────────────────────
    # Compliance can comment breaches (RM channel) + export CSSF reports
    # head_of can validate too (they formally close the CSSF notification loop)
    matrix += [("Compliance", "intern",  base_view + compliance_view)]
    matrix += [("Compliance", "analyst", base_view + compliance_view + risk_export + compliance_export)]
    matrix += [("Compliance", "officer", base_view + compliance_view + risk_export + compliance_export + breach_rm_comment + client_read)]
    matrix += [("Compliance", "senior",  base_view + compliance_view + risk_export + compliance_export + breach_rm_comment + client_read + client_write)]
    matrix += [("Compliance", "deputy",  base_view + compliance_view + risk_export + compliance_export + breach_rm_comment + breach_rm_validate + client_read + client_write + fund_cfg_view)]
    matrix += [("Compliance", "head_of", base_view + compliance_view + risk_export + compliance_export + breach_rm_comment + breach_rm_validate + breach_run + client_read + client_write + fund_cfg_view + user_view)]

    # ── Sales (Monaco) ───────────────────────────────────────────
    # No risk access, no client fund access
    matrix += [("Sales", "intern",     ["page.portfolio.view"])]
    matrix += [("Sales", "analyst",    ["page.portfolio.view"] + port_export)]
    matrix += [("Sales", "officer",    ["page.portfolio.view"] + port_export)]  # "advisor"
    matrix += [("Sales", "senior",     ["page.portfolio.view"] + port_export)]
    matrix += [("Sales", "head_of",    ["page.portfolio.view"] + port_export + user_view + fund_cfg_view)]

    # ── Advisory (Monaco) ────────────────────────────────────────
    matrix += [("Advisory", "intern",  ["page.portfolio.view"])]
    matrix += [("Advisory", "analyst", ["page.portfolio.view"] + port_export + client_read)]
    matrix += [("Advisory", "officer", ["page.portfolio.view", "page.risk.view"] + port_export + risk_export + client_read)]
    matrix += [("Advisory", "senior",  ["page.portfolio.view", "page.risk.view"] + port_export + risk_export + client_read + client_write)]
    matrix += [("Advisory", "head_of", ["page.portfolio.view", "page.risk.view"] + port_export + risk_export
                                        + client_read + client_write + fund_cfg_view + user_view)]

    # ── Board / Direction Générale ───────────────────────────────
    # Read-only everywhere + can annotate breach for DG attention
    # No write, no run, no validate
    board_view = (base_view + compliance_view + ["page.administration.view"]
                  + risk_export + port_export + compliance_export
                  + org_view + fund_cfg_view + client_read + user_view
                  + ["breach.escalate.board"])
    matrix += [("Board", "board_member",   board_view)]
    matrix += [("Board", "board_director", board_view)]

    # ── Admin ────────────────────────────────────────────────────
    # ALL positions in Admin get ALL permissions.
    # intern in Admin = full admin. Intentional.
    all_perms = [p[0] for p in PERMISSION_SEED]
    for pos_name in ["intern", "analyst", "officer", "senior", "deputy", "head_of", "admin"]:
        matrix += [("Admin", pos_name, all_perms)]

    return matrix


DEPT_POSITION_PERMS_SEED = _build_dept_position_perms()


# ── Controls (unchanged from v4) ─────────────────────────────────────

def z(order, label, color, lo, lo_inc, hi, hi_inc, is_sym, action, notify, cssf_h=None):
    return {"zone_order": order, "label": label, "color_rgba": color,
            "is_symmetric": is_sym, "lower_bound": lo, "lower_inclusive": lo_inc,
            "upper_bound": hi, "upper_inclusive": hi_inc, "action_description": action,
            "notify_roles": notify, "cssf_notify_hours": cssf_h}

W=  "white";  G="rgba(0,255,0,0.3)";   Y="rgba(255,255,0,0.3)"
O=  "rgba(255,165,0,0.3)";  R="rgba(255,0,0,0.3)";  DG="rgba(0,128,0,0.4)"
N_=[]; RM_=["RM"]; RM_PM=["RM","PM"]; RM_A=["RM","AIFM"]
RM_PM_A=["RM","PM","AIFM"]; RM_A_M_C=["RM","AIFM","Management","CSSF"]; RM_PM_M=["RM","PM","Management"]

CONTROL_SEED = [
    {"code":"L01","category":"leverage","tab_label":"Leverage","name":"Leverage Risk — Fund Level","description":"Gross and Commitment Leverage at fund level. Hard limit 300%.","zones":[
        z(1,"Normal",W,0,1,275,1,0,"Normal range. No action required.",N_),
        z(2,"Internal Alert",DG,275,0,290,1,0,"Internal alert. Risk team documents position rationale.",RM_),
        z(3,"Pre-Breach",O,290,0,300,1,0,"Pre-breach zone. Formal escalation to AIFM risk officer.",RM_A),
        z(4,"Hard Breach",R,300,0,None,0,0,"Hard breach. Immediate notification. CSSF within 48h.",RM_A_M_C,cssf_h=48)],"metrics":[
        {"metric_name":"Gross Leverage","column_source":"Value","unit":"%","is_absolute":0},
        {"metric_name":"Commitment Leverage","column_source":"Value","unit":"%","is_absolute":0}]},
    {"code":"L02","category":"leverage","tab_label":"Leverage","name":"Leverage Risk — Underlying Level","description":"Delta/NAV% per underlying. Symmetric.","zones":[
        z(1,"Normal",W,0,1,25,1,1,"Normal – no action required. x ∈ [-25;25]",N_),
        z(2,"Monitoring",O,25,0,30,1,1,"Monitoring – justification logged. x ∈ [-30;-25]∪[25;30]",RM_),
        z(3,"Breach",R,30,0,None,0,1,"Breach – formal escalation. |Delta/NAV%| > 30%",RM_A)],"metrics":[
        {"metric_name":"Delta/NAV%","column_source":"Delta/NAV%","unit":"%","is_absolute":0}]},
    {"code":"L03","category":"leverage","tab_label":"Leverage","name":"Leverage Risk — Position Level","description":"Exposure % NAV per trade. Symmetric.","zones":[
        z(1,"Normal",G,0,1,25,1,1,"Normal – no action required. x ∈ [-25;25]",N_),
        z(2,"Monitoring",O,25,0,30,1,1,"Monitoring – justification logged.",RM_),
        z(3,"Breach",R,30,0,None,0,1,"Breach – formal escalation. |Exposure% NAV| > 30%",RM_A)],"metrics":[
        {"metric_name":"Exposure % NAV","column_source":"Exposure % NAV","unit":"%","is_absolute":0}]},
    {"code":"S01","category":"var_simm","tab_label":"VaR & SIMM","name":"VaR/SIMM — SIMM/NAV Ratio","description":"SIMM as % of NAV. Hard limit 20%.","zones":[
        z(1,"Normal",W,0,1,18,1,0,"Normal.",N_),
        z(2,"Pre-Breach",O,18,0,20,1,0,"Pre-breach – Escalation to AIFM Risk Officer.",RM_A),
        z(3,"Breach",R,20,0,None,0,0,"Breach – Immediate escalation. Documented in Risk Committee.",RM_A)],"metrics":[
        {"metric_name":"SIMM/NAV%","column_source":"simm_nav_ratio","unit":"%","is_absolute":0}]},
    {"code":"S02","category":"var_simm","tab_label":"VaR & SIMM","name":"VaR/SIMM — Initial Margin","description":"Initial Margin per counterparty bank.","zones":[
        z(1,"Low Risk",G,0,1,9_500_000,0,0,"Normal.",N_),
        z(2,"Moderate Risk",O,9_500_000,1,10_000_000,0,0,"Monitoring – justification logged.",RM_),
        z(3,"High Risk",R,10_000_000,1,None,0,0,"Breach – formal escalation.",RM_A)],"metrics":[
        {"metric_name":"Initial Margin","column_source":"IM","unit":"EUR","is_absolute":0}]},
    {"code":"S03","category":"var_simm","tab_label":"VaR & SIMM","name":"VaR/SIMM — Variation Margin","description":"Variation Margin per counterparty bank.","zones":[
        z(1,"Low Risk",G,0,1,1_750_000,0,0,"Normal.",N_),
        z(2,"Moderate Risk",O,1_750_000,1,2_000_000,0,0,"Monitoring.",RM_),
        z(3,"High Risk",R,2_000_000,1,None,0,0,"Breach – formal escalation.",RM_A)],"metrics":[
        {"metric_name":"Variation Margin","column_source":"VM","unit":"EUR","is_absolute":0}]},
    {"code":"D01","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Delta","description":"Delta/NAV% per underlying. Symmetric.","zones":[
        z(1,"Normal",W,0,1,25,1,1,"Normal.",N_),z(2,"Monitoring",O,25,0,30,1,1,"Monitoring.",RM_),
        z(3,"Breach",R,30,0,None,0,1,"Breach.",RM_A)],"metrics":[
        {"metric_name":"Delta/NAV%","column_source":"Delta/NAV%","unit":"%","is_absolute":0}]},
    {"code":"GEQ","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Gamma Equity Stocks","description":"Gamma % vs weighted soft limit. Notional > 50k.","zones":[
        z(1,"Normal",W,0,1,80,1,0,"Normal.",N_),z(2,"Alert",O,80,0,100,1,0,"Alert.",RM_),
        z(3,"Breach",R,100,0,None,0,0,"Escalation required.",RM_A)],"metrics":[
        {"metric_name":"Gamma % (ratio to soft limit)","column_source":"Gamma %","unit":"%","is_absolute":0}]},
    {"code":"GEQIDX","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Gamma Equity Index","description":"Gamma % vs soft limit per index. Notional > 1M.","zones":[
        z(1,"Normal",W,0,1,80,1,0,"Normal.",N_),z(2,"Alert",O,80,0,100,1,0,"Alert.",RM_),
        z(3,"Breach",R,100,0,None,0,0,"Escalation required.",RM_A)],"metrics":[
        {"metric_name":"Gamma % (ratio to soft limit)","column_source":"Gamma %","unit":"%","is_absolute":0}]},
    {"code":"GFX","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Gamma Forex","description":"Gamma % for FX options. Gross Notional > 50k.","zones":[
        z(1,"Normal",W,0,1,80,1,0,"Normal.",N_),z(2,"Alert",O,80,0,100,1,0,"Alert.",RM_),
        z(3,"Breach",R,100,0,None,0,0,"Escalation required.",RM_A)],"metrics":[
        {"metric_name":"Gamma %","column_source":"Gamma %","unit":"%","is_absolute":0}]},
    {"code":"DGFX","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Delta-Gamma Adjusted FX","description":"Delta-Gamma Adjusted % for FX. Symmetric. 4 zones.","zones":[
        z(1,"Normal",W,0,1,20,0,1,"Normal. |DGFX| < 20%",N_),
        z(2,"Alert — Notify RM",O,20,1,25,0,1,"Alert – Notify RM.",RM_),
        z(3,"Alert — Notify RM+PM",Y,25,1,30,0,1,"Alert – Notify RM+PM.",RM_PM),
        z(4,"Breach",R,30,1,None,0,1,"Escalation required. |DGFX| ≥ 30%",RM_PM_A)],"metrics":[
        {"metric_name":"Delta-Gamma Adjusted %","column_source":"Delta-Gamma Adjusted %","unit":"%","is_absolute":0}]},
    {"code":"V01","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Vega Fund Level","description":"Vega/NAV% at fund level. Equity and FX.","zones":[
        z(1,"Normal",G,0,1,1.0,1,0,"Standard monitoring.",N_),
        z(2,"Monitoring",O,1.0,0,2.5,1,0,"Monitoring – justification logged.",RM_),
        z(3,"Breach",R,2.5,0,None,0,0,"Breach – formal escalation.",RM_PM_A)],"metrics":[
        {"metric_name":"Vega/NAV% Equity","column_source":"vega_eq","unit":"%","is_absolute":0},
        {"metric_name":"Vega/NAV% FX","column_source":"vega_fx","unit":"%","is_absolute":0}]},
    {"code":"V02","category":"sensitivity","tab_label":"Sensitivities","name":"Portfolio Sensitivities — Vega Underlying Level","description":"Vega/NAV% per underlying. Symmetric.","zones":[
        z(1,"Normal",W,0,1,1.0,1,1,"Normal. |Vega/NAV%| ≤ 1%",N_),
        z(2,"Monitoring",O,1.0,0,2.5,1,1,"Monitoring.",RM_),
        z(3,"Breach",R,2.5,0,None,0,1,"Breach.",RM_PM_A)],"metrics":[
        {"metric_name":"Vega/NAV%","column_source":"Vega/NAV%","unit":"%","is_absolute":0}]},
    {"code":"PL01","category":"pnl","tab_label":"P&L","name":"P&L Move Control — Fund Level","description":"1D Change in NAV/GAV at fund level. Symmetric.","zones":[
        z(1,"Normal",W,0,1,0.5,1,1,"Normal.",N_),
        z(2,"Risk Team Notified",G,0.5,0,1.0,1,1,"Risk team notified.",RM_),
        z(3,"Formal Review",O,1.0,0,2.0,1,1,"Formal review by RM.",RM_),
        z(4,"Executive Escalation",R,2.0,0,None,0,1,"Executive escalation within 24h.",RM_PM_M)],"metrics":[
        {"metric_name":"1D Change (GAV)","column_source":"1D Change","unit":"%","is_absolute":0}]},
    {"code":"PL02","category":"pnl","tab_label":"P&L","name":"P&L Move Control — Book Level","description":"1D Change in MV per book. Symmetric.","zones":[
        z(1,"Normal",W,0,1,0.35,1,1,"Normal.",N_),
        z(2,"Risk Team Notified",G,0.35,0,0.50,1,1,"Risk team notified.",RM_),
        z(3,"Formal Review",O,0.50,0,0.75,1,1,"Formal review by RM.",RM_),
        z(4,"Executive Escalation",R,0.75,0,None,0,1,"Executive escalation.",RM_PM_M)],"metrics":[
        {"metric_name":"1D Change (Book)","column_source":"1D Change","unit":"%","is_absolute":0}]},
    {"code":"CR01","category":"counterparty","tab_label":"Counterparty","name":"Counterparty Risk — Concentration","description":"MV/NAV% per counterparty.","zones":[
        z(1,"Normal",W,0,1,25,1,0,"Normal.",N_),z(2,"Warning",O,25,0,28,1,0,"Warning.",RM_),
        z(3,"Critical",R,28,0,None,0,0,"Critical – Breach.",RM_A)],"metrics":[
        {"metric_name":"MV/NAV%","column_source":"MV/NAV%","unit":"%","is_absolute":0}]},
    {"code":"CR02","category":"credit","tab_label":"Credit","name":"Credit Risk — Concentration","description":"MV/NAV% per issuer.","zones":[
        z(1,"Normal",W,0,1,25,1,0,"Normal.",N_),z(2,"Warning",O,25,0,28,1,0,"Warning.",RM_),
        z(3,"Critical",R,28,0,None,0,0,"Critical – Breach.",RM_A)],"metrics":[
        {"metric_name":"MV/NAV%","column_source":"MV/NAV%","unit":"%","is_absolute":0}]},
    {"code":"CS01","category":"credit","tab_label":"Credit","name":"Credit Risk — CS01 Sensitivity","description":"CS01/NAV% per issuer. Symmetric.","zones":[
        z(1,"Normal",W,0,1,0.01,1,1,"Normal.",N_),
        z(2,"Monitoring",O,0.01,0,0.02,1,1,"1bp threshold.",RM_),
        z(3,"Breach",R,0.02,0,None,0,1,"2bp threshold – escalation.",RM_A)],"metrics":[
        {"metric_name":"CS01/NAV%","column_source":"CS01/NAV%","unit":"bp","is_absolute":0}]},
    {"code":"LR01","category":"counterparty","tab_label":"Counterparty","name":"Counterparty Risk — Delta Exposure","description":"Delta/NAV% per counterparty. Symmetric.","zones":[
        z(1,"Normal",W,0,1,25,1,1,"Normal.",N_),z(2,"Monitoring",O,25,0,30,1,1,"Monitoring.",RM_),
        z(3,"Breach",R,30,0,None,0,1,"Breach.",RM_A)],"metrics":[
        {"metric_name":"Delta/NAV%","column_source":"Delta/NAV%","unit":"%","is_absolute":0}]},
    {"code":"OL1","category":"operational","tab_label":"Operational","name":"Operational Risk Control","description":"TBD.","zones":[],"metrics":[]},
    {"code":"ESG1","category":"esg","tab_label":"ESG","name":"Sustainability & ESG Risk","description":"TBD.","zones":[],"metrics":[]},
]


# ════════════════════════════════════════════════════════════════════
# Seed functions
# ════════════════════════════════════════════════════════════════════

def seed_departments(cur):
    for name, display, client_access, cross_office, desc in DEPARTMENT_SEED:
        cur.execute(
            "INSERT OR IGNORE INTO departments (name,display_name,can_access_client_funds,can_cross_offices,description) VALUES (?,?,?,?,?)",
            (name, display, client_access, cross_office, desc))

def seed_positions(cur):
    for name, display, rank, desc in POSITION_SEED:
        cur.execute(
            "INSERT OR IGNORE INTO positions (name,display_name,seniority_rank,description) VALUES (?,?,?,?)",
            (name, display, rank, desc))

def seed_sections(cur):
    for slug, display, icon, order in SECTION_SEED:
        cur.execute(
            "INSERT OR IGNORE INTO sections (slug,display_name,icon,sort_order) VALUES (?,?,?,?)",
            (slug, display, icon, order))

def seed_pages(cur):
    for section_slug, slug, display, order, desc in PAGE_SEED:
        sect_id = cur.execute("SELECT id FROM sections WHERE slug=?", (section_slug,)).fetchone()[0]
        cur.execute(
            "INSERT OR IGNORE INTO pages (section_id,slug,display_name,sort_order,description) VALUES (?,?,?,?,?)",
            (sect_id, slug, display, order, desc))

def seed_permissions(cur):
    for code, domain, resource, action, desc in PERMISSION_SEED:
        cur.execute(
            "INSERT OR IGNORE INTO permissions (code,domain,resource,action,description) VALUES (?,?,?,?,?)",
            (code, domain, resource, action, desc))

def seed_dept_position_perms(cur):
    for dept_name, pos_name, perm_codes in DEPT_POSITION_PERMS_SEED:
        dept_id = cur.execute("SELECT id FROM departments WHERE name=?", (dept_name,)).fetchone()
        pos_id  = cur.execute("SELECT id FROM positions  WHERE name=?", (pos_name,)).fetchone()
        if not dept_id or not pos_id:
            continue
        for code in set(perm_codes):  # deduplicate
            perm_id = cur.execute("SELECT id FROM permissions WHERE code=?", (code,)).fetchone()
            if not perm_id:
                continue
            cur.execute(
                "INSERT OR IGNORE INTO dept_position_perms (department_id,position_id,permission_id,org_id) VALUES (?,?,?,NULL)",
                (dept_id[0], pos_id[0], perm_id[0]))

def seed_controls(cur):
    for ctrl in CONTROL_SEED:
        cur.execute(
            "INSERT OR IGNORE INTO control_definitions (code,name,category,tab_label,description,org_id) VALUES (?,?,?,?,?,NULL)",
            (ctrl["code"], ctrl["name"], ctrl["category"], ctrl["tab_label"], ctrl["description"]))
        ctrl_id = cur.execute("SELECT id FROM control_definitions WHERE code=? AND org_id IS NULL", (ctrl["code"],)).fetchone()[0]
        for zone in ctrl["zones"]:
            cur.execute(
                "INSERT OR IGNORE INTO control_zones (control_id,zone_order,label,color_rgba,is_symmetric,lower_bound,lower_inclusive,upper_bound,upper_inclusive,action_description,notify_roles,cssf_notify_hours) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (ctrl_id,zone["zone_order"],zone["label"],zone["color_rgba"],zone["is_symmetric"],zone["lower_bound"],zone["lower_inclusive"],zone["upper_bound"],zone["upper_inclusive"],zone["action_description"],json.dumps(zone["notify_roles"]),zone["cssf_notify_hours"]))
        for m in ctrl["metrics"]:
            cur.execute(
                "INSERT OR IGNORE INTO control_metrics (control_id,metric_name,column_source,unit,is_absolute) VALUES (?,?,?,?,?)",
                (ctrl_id, m["metric_name"], m["column_source"], m["unit"], m["is_absolute"]))


# ════════════════════════════════════════════════════════════════════
# Zone evaluation helpers
# ════════════════════════════════════════════════════════════════════

def evaluate_zone(value: float, zone: dict) -> bool:
    v = abs(value) if zone["is_symmetric"] else value
    lo, lo_inc = zone["lower_bound"], zone["lower_inclusive"]
    hi, hi_inc = zone["upper_bound"], zone["upper_inclusive"]
    lower_ok = (lo is None) or (v >= lo if lo_inc else v > lo)
    upper_ok = (hi is None) or (v <= hi if hi_inc else v < hi)
    return lower_ok and upper_ok

def find_zone(value: float, zones: list) -> dict | None:
    for zone in sorted(zones, key=lambda z: z["zone_order"]):
        if evaluate_zone(value, zone):
            return zone
    return None


# ════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════

def get_db_path(db_url):
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///"):]
    raise ValueError(f"Unsupported DB URL: {db_url!r}")

def create_schema(cur):
    created = []
    for stmt in DDL_STATEMENTS:
        stmt = stmt.strip()
        if not stmt: continue
        cur.execute(stmt)
        words = stmt.split()
        if len(words) >= 6 and words[0].upper() == "CREATE":
            created.append(words[5])
    return created

def create_database(db_path: str, verbose: bool = True):
    parent = os.path.dirname(db_path)
    if parent: os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")

    created = create_schema(cur)
    seed_departments(cur)
    seed_positions(cur)
    seed_sections(cur)
    seed_pages(cur)
    seed_permissions(cur)
    seed_dept_position_perms(cur)
    seed_controls(cur)
    conn.commit()
    conn.close()

    if verbose:
        total_dpp = sum(len(set(p)) for _, _, p in DEPT_POSITION_PERMS_SEED)
        total_zones   = sum(len(c["zones"])   for c in CONTROL_SEED)
        total_metrics = sum(len(c["metrics"]) for c in CONTROL_SEED)
        sym  = sum(1 for c in CONTROL_SEED for z in c["zones"] if z["is_symmetric"])
        asym = sum(1 for c in CONTROL_SEED for z in c["zones"] if not z["is_symmetric"])

        print(f"\n[+] Database ready: {db_path}  [v6]")
        print(f"\n    Schema  — {len(created)} objects")
        print(f"\n    Seed:")
        print(f"        {len(DEPARTMENT_SEED):3}  departments")
        print(f"        {len(POSITION_SEED):3}  positions")
        print(f"        {len(SECTION_SEED):3}  sections")
        print(f"        {len(PAGE_SEED):3}  pages")
        print(f"        {len(PERMISSION_SEED):3}  permissions (atomic actions)")
        print(f"        {total_dpp:3}  dept×position permission assignments")
        print(f"        {len(CONTROL_SEED):3}  control definitions")
        print(f"        {total_zones:3}  control zones ({sym} symmetric | {asym} non-sym)")
        print(f"        {total_metrics:3}  control metrics")
        print(f"""
    Breach workflow (v6):
      status:   open → under_review → resolved | escalated | cssf_notified | reopened
      comments: RM officer+ can comment  (breach.comment.rm)
                PM officer+ can comment  (breach.comment.pm)  same org as fund
                Both: no limit on number of comments
      validate: ONLY RM (dept=RM, rank >= 5 deputy/head_of)  (breach.validate)
                Compliance head_of/deputy can also validate (CSSF loop closure)
      Board:    read + breach.escalate.board annotation only, never validates

    Admin dept (v6):
      ALL positions in Admin = ALL permissions
      intern in Admin = full admin. Intentional.
      Provider Admin (org=Heroics) → all orgs + all client funds
      Client Admin   (org=ClientX) → own org only (app-side enforcement)

    Attachments:
      breach_attachments: path on disk (N:\\AEGIS\\ATTACHMENTS\\breaches\\{{id}}\\)
      Linked to breach_id and optionally to a specific comment_id
        """)
        print(f"""
    Key tables:
      organisations   → funds → fund_data_paths
      offices         → dept_office_map
      departments     → dept_position_map → dept_position_perms
      positions       ↗
      users           → user_fund_access (explicit client fund grants)
                      → user_permission_overrides (per-user exceptions)
      sections → pages → page_required_perms → permissions
      control_breaches → breach_comments (user_id + dept_id + pos_id)

    3 admin types:
      Provider Admin   (org=Heroics, dept=Admin, pos=admin)
                       Full access: all orgs, all funds
      Client Admin     (org=ClientXYZ, dept=Admin, pos=admin)
                       Full access within their org only
      Board/DG         (dept=Board, pos=board_director)
                       Read-only everywhere, no write/run

    Client fund access (provider side):
      position.seniority_rank >= 3 (officer+)
      AND department.can_access_client_funds = 1
      AND explicit entry in user_fund_access
      Exception: Admin → automatic, no entry needed

    → Next steps:
        1. INSERT your provider org + offices
        2. INSERT funds + fund_data_paths per client
        3. INSERT users with office_id + department_id + position_id
        4. GRANT user_fund_access for provider staff on client funds
        5. python scripts/migrate_nav_to_db.py
        6. AEGIS_USE_DB=true in .env
        """)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--tenant")
    args = parser.parse_args()
    if args.db_path:
        db_path = args.db_path
    else:
        try:
            from src.config.tenant import load_tenant_config
            config = load_tenant_config(args.tenant)
            if not config.db_url:
                print("[!] AEGIS_DB_URL not set."); sys.exit(1)
            db_path = get_db_path(config.db_url)
        except ImportError:
            print("[!] Use --db-path."); sys.exit(1)
    create_database(db_path)

if __name__ == "__main__":
    main()