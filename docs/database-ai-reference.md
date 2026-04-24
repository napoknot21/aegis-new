# Aegis Database Reference For Claude

Date: 2026-04-17

## Purpose

This document is a current-state database reference for an AI assistant that needs to reason about the Aegis schema safely.

It is meant to answer:

- which tables currently exist
- what each table is for
- how the main relationships work
- which parts of the schema are actively used by the backend
- which gaps are still transitional, so bad recommendations can be avoided

## Source Of Truth

If there is any contradiction, trust the repo in this order:

1. `supabase/migrations/`
2. `src/backend/app/infrastructure/persistence/postgres/`
3. `src/backend/app/domain/`
4. `supabase/tests/`
5. `supabase/seed.sql`
6. `supabase/drafts/`
7. older narrative docs

Important consequence:

- `supabase/migrations/` is the canonical schema history
- `supabase/tests/` confirms which invariants are already enforced
- the backend code shows which tables are actually used in runtime flows

## Runtime Architecture Assumption

Current intended runtime flow:

`Frontend -> FastAPI backend -> Postgres inside Supabase`

Implications:

- the browser is not supposed to query core business tables directly
- the backend is the real business API
- direct `anon` and `authenticated` access to `public` has been revoked
- there is no RLS yet, so the current security posture is "backend-only access" rather than "browser-safe SQL access"

## Cross-Cutting Modeling Rules

- Tenant boundary is `organisation`, carried by `id_org`.
- Tenant-scoped relations usually include composite keys such as `(id_org, id_f)` or `(id_org, id_user)`.
- Shared references are global, mainly `currencies` and `asset_classes`.
- Most tables use a numeric primary key for operations plus a secondary `uuid` for external stability.
- The main trade aggregate is `trades` + `trade_disc` + `trade_disc_legs` + optional one-to-one child tables per leg.
- Reporting datasets follow a repeated pattern: one snapshot header table plus one row table.
- Intraday reporting batches are grouped by `ingestion_runs`.
- `SIMM` is daily and independent from `ingestion_runs`.
- `AUM` is daily and modeled like `SIMM`, but its `id_run` is not linked to `ingestion_runs`.

## Schema Size

Committed migrations currently create 47 tables, grouped into these families:

1. Shared references: 2 tables
2. Tenant and authz foundation: 11 tables
3. Trade core: 15 tables
4. Reporting orchestration: 1 table
5. Reporting snapshots: 18 tables

## Family 1: Shared Reference Tables

These tables are global and not tenant-scoped.

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `currencies` | Master currency list used across funds, trade legs, premiums, settlements, expiries, and AUM. | PK `id_ccy`; unique `code`; seeded locally; has `is_active`, `sort_order`, `updated_at`. |
| `asset_classes` | Master asset class list used across trade legs and several reporting datasets. | PK `id_ac`; unique `code`, `name`, `ice_code`; seeded locally; has `is_active`, `sort_order`, `updated_at`. |

## Family 2: Tenant And Authz Foundation

These tables define the tenant model and the future authorization model. Authentication is still handled outside the database.

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `organisations` | Root tenant table. Most business tables ultimately hang off this. | PK `id_org`; unique `code`; tenant root. |
| `offices` | Office locations inside an organisation. | FK to `organisations`; unique office `code` and `name` per org. |
| `departments` | Department catalog per organisation. | FK to `organisations`; unique `code` and `name` per org. |
| `office_departments` | Mapping between offices and departments. | Composite org-aware FKs to `offices` and `departments`; supports `is_primary`. |
| `users` | Application user directory per organisation. | Stores `entra_oid`, `email`, `display_name`; unique email and Entra OID per org. |
| `user_offices` | User-to-office assignment. | Org-aware join table; supports `is_primary` and `is_active`. |
| `user_departments` | User-to-office_department assignment. | Org-aware join table; supports `is_primary` and `is_active`. |
| `ranks` | Rank catalog per organisation. | Unique `code` and `rank_level` per org. |
| `user_ranks` | User-to-rank assignment. | Org-aware join table; supports `is_primary` and `is_active`. |
| `access_roles` | Access role catalog per organisation. | Unique `code` per org; intended for authorization metadata. |
| `user_access_roles` | User-to-role assignment. | Org-aware join table for permission membership. |

Important notes for this family:

- The database already anticipates a real user and role model.
- There is still no link from this `users` table to Supabase `auth.users`.
- Hardening migration adds single-primary guarantees for office, department, and rank assignments.
- Email uniqueness is enforced case-insensitively within each organisation.

## Family 3: Trade Core

This is the most concrete business model in the current app.

### Trade Reference And Scoping Tables

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `funds` | Fund reference per organisation. | FK to `organisations` and `currencies`; unique `code` per org; carries `fund_type`. |
| `fund_office_access` | Which offices can access a fund. | Join between `funds` and `offices`; `access_type` is `primary` or `secondary`. |
| `banks` | Bank catalog per organisation. | Unique `code` per org. |
| `counterparties` | Counterparty catalog per organisation, optionally linked to a bank. | FK to `banks`; unique `ext_code` per org; used by trade and reporting datasets. |
| `books` | Book hierarchy per fund. | FK to `funds`; self-reference via `parent_id`; unique `name` per fund. |
| `trade_types` | Trade type catalog per organisation. | Unique `code` per org; backend currently initializes `DISC` and `ADV`. |
| `trade_disc_labels` | Label catalog for discretionary trades. | Unique `code` per org; used by DISC trades. |

### Trade Aggregate Tables

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `trade_spe` | Shared identity anchor for a trade subtree. | Minimal table used as a stable trade root by org. |
| `trades` | Trade header table. | References `trade_spe`, `trade_types`, `funds`, and optional booking users; holds `status`. |
| `trade_disc` | DISC-specific detail row for a trade. | One row per DISC trade; references `books`, optional `portfolio`, `counterparties`, and `trade_disc_labels`. |
| `trade_disc_legs` | Legs under a DISC trade. | One-to-many from `trade_disc`; references `asset_classes` and `currencies`; unique `leg_id` per trade. |
| `trade_disc_instruments` | Optional instrument details for one leg. | One-to-one with a leg; cascades on leg delete. |
| `trade_disc_fields` | Optional field-level details for one leg. | One-to-one with a leg; contains `buysell`, dates, notionals, payout currency. |
| `trade_disc_premiums` | Optional premium details for one leg. | One-to-one with a leg; amount, currency, date, markup, total. |
| `trade_disc_settlements` | Optional settlement details for one leg. | One-to-one with a leg; settlement date, currency, type. |

Important notes for this family:

- `trade_disc` is keyed by `id_spe`, so it behaves like a trade subtype table.
- `trade_disc(id_org, id_spe)` is explicitly tied back to `trades(id_org, id_spe)` by the hardening migration.
- The schema currently supports DISC end to end.
- `ADV` exists in the trade type catalog, but there is no separate advisory trade aggregate yet.
- The pgTAP tests verify that one DISC trade can own multiple legs and that each optional child table stays one-to-one with a leg.

## Family 4: Reporting Orchestration

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `ingestion_runs` | Parent record for one logical intraday reporting batch. | Linked to one org and fund; child intraday snapshot headers reference `(id_org, id_f, id_run)`; deleting a run cascades to its child headers and rows. |

Important notes:

- `run_type` is currently `reporting_snapshot` or `reporting_snapshot_partial`.
- This table does not govern daily `SIMM`.
- This table does not currently govern `AUM`.

## Family 5: Reporting Snapshots

The reporting model repeats one main pattern:

- a snapshot header table stores metadata, status, official flag, load information, and row counts
- a row table stores the actual business rows for that dataset

### Daily Snapshot Families

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `simm_snapshots` | Daily SIMM snapshot header. | One official snapshot per fund/day is enforced; stores source metadata and `row_count`. |
| `simm_snapshot_rows` | Rows under one SIMM snapshot. | Usually one row per counterparty; aligned to parent by org, fund, and date; cascades on snapshot delete. |
| `aum_snapshots` | Daily AUM snapshot header. | Same discipline as SIMM; one official snapshot per fund/day; has `id_run` but no FK to `ingestion_runs`. |
| `aum_rows` | Single row under one AUM snapshot. | One-to-one with snapshot; stores `aum_value`, currency, valuation timestamp, and raw payload. |

### Intraday Snapshot Families

| Table | Purpose | Main keys and notes |
| --- | --- | --- |
| `expiries_snapshots` | Header for an expiries file import. | Intraday dataset; linked to `ingestion_runs`; uses `snapshot_date` and `snapshot_ts`. |
| `expiries` | Expiries rows under one snapshot. | One row per imported structure or position; unique by `row_hash` within snapshot. |
| `nav_estimated_snapshots` | Header for estimated NAV snapshot loads. | Intraday dataset; linked to `ingestion_runs`; supports official flag. |
| `nav_estimated` | Single NAV row under one snapshot. | One row per snapshot after hardening. |
| `leverages_snapshots` | Header for leverage summary loads. | Intraday dataset; linked to `ingestion_runs`. |
| `leverages` | Single leverage summary row under one snapshot. | One row per snapshot after hardening. |
| `leverages_per_trade_snapshots` | Header for leverage-by-trade loads. | Intraday dataset; linked to `ingestion_runs`. |
| `leverages_per_trade` | Trade-level leverage rows. | Usually one row per `trade_id` within snapshot; also references asset class and optional counterparty. |
| `leverages_per_underlying_snapshots` | Header for leverage-by-underlying loads. | Intraday dataset; linked to `ingestion_runs`. |
| `leverages_per_underlying` | Underlying-level leverage rows. | One row per underlying within a snapshot in practice; stores leverage and exposure metrics. |
| `long_short_delta_snapshots` | Header for long/short delta loads. | Intraday dataset; linked to `ingestion_runs`. |
| `long_short_delta` | Underlying-level long/short delta rows. | Unique per underlying within a snapshot after hardening. |
| `counterparty_concentration_snapshots` | Header for counterparty concentration loads. | Intraday dataset; linked to `ingestion_runs`. |
| `counterparty_concentration` | Counterparty-level concentration rows. | Unique per counterparty within a snapshot after hardening. |

### Reporting Dataset Semantics

| Dataset | Header table | Row table | Shape | Notes |
| --- | --- | --- | --- | --- |
| `AUM` | `aum_snapshots` | `aum_rows` | Single-row | Daily, official-per-day, not linked to `ingestion_runs`. |
| `SIMM` | `simm_snapshots` | `simm_snapshot_rows` | Multi-row | Daily, independent from `ingestion_runs`, usually grouped by counterparty. |
| `EXPIRIES` | `expiries_snapshots` | `expiries` | Multi-row | Intraday, file-oriented, grouped under `ingestion_runs`. |
| `NAV_ESTIMATED` | `nav_estimated_snapshots` | `nav_estimated` | Single-row | Intraday, one row per snapshot. |
| `LEVERAGES` | `leverages_snapshots` | `leverages` | Single-row | Intraday, one row per snapshot. |
| `LEVERAGES_PER_TRADE` | `leverages_per_trade_snapshots` | `leverages_per_trade` | Multi-row | Intraday, one row per trade in practice. |
| `LEVERAGES_PER_UNDERLYING` | `leverages_per_underlying_snapshots` | `leverages_per_underlying` | Multi-row | Intraday, one row per underlying in practice. |
| `LONG_SHORT_DELTA` | `long_short_delta_snapshots` | `long_short_delta` | Multi-row | Intraday, one row per underlying. |
| `COUNTERPARTY_CONCENTRATION` | `counterparty_concentration_snapshots` | `counterparty_concentration` | Multi-row | Intraday, one row per counterparty. |

## Important Invariants Already Enforced

These are not just design intentions. They are backed by migrations and pgTAP tests.

- `anon` and `authenticated` do not have direct access to business tables in `public`.
- `service_role` keeps backend-style access.
- One user can have only one active primary office.
- One office can have only one active primary department mapping.
- One user can have only one active primary rank.
- One fund can have only one active primary office access row.
- `trade_disc` must match an existing `trades` header through `(id_org, id_spe)`.
- `trade_disc_fields.buysell` is normalized to `Buy` or `Sell`.
- Optional DISC leg child tables stay one-to-one with a leg.
- Deleting a DISC leg cascades to its optional child rows.
- `SIMM` allows multiple retries per fund/day, but only one official snapshot per fund/day.
- Snapshot rows are aligned with their parent header using composite org-aware FKs.
- `nav_estimated` and `leverages` are enforced as one-row-per-snapshot datasets.
- `long_short_delta` is unique per snapshot and underlying.
- `counterparty_concentration` is unique per snapshot and counterparty.
- Deleting an `ingestion_runs` parent cascades through intraday snapshot headers and rows, but does not delete SIMM data.

## What The Backend Actively Uses Today

### Reference endpoints

Actively queried by the backend:

- `currencies`
- `asset_classes`
- `funds`
- `books`
- `trade_disc_labels`
- `counterparties`

### Trade endpoints

Actively queried or written by the backend:

- `trade_types`
- `trade_spe`
- `trades`
- `trade_disc`
- `trade_disc_legs`
- `trade_disc_instruments`
- `trade_disc_fields`
- `trade_disc_premiums`
- `trade_disc_settlements`

### Data snapshot endpoints

The generic snapshot API currently registers all of these datasets:

- `AUM`
- `SIMM`
- `EXPIRIES`
- `NAV_ESTIMATED`
- `LEVERAGES`
- `LEVERAGES_PER_TRADE`
- `LEVERAGES_PER_UNDERLYING`
- `LONG_SHORT_DELTA`
- `COUNTERPARTY_CONCENTRATION`

### Non-canonical risk area

The backend exposes a `risk` route that reads:

- `risk_categories`
- `risk_control_definitions`
- `risk_control_levels`

Those tables are not present in the committed Supabase migration history, so that area should be treated as transitional or placeholder, not canonical.

## Current Seed Coverage

`supabase/seed.sql` currently seeds only:

- `currencies`
- `asset_classes`

It does not seed tenant-specific rows like:

- `organisations`
- `users`
- `funds`
- `books`
- `counterparties`
- `trade_disc_labels`

So empty responses on tenant-scoped endpoints do not automatically mean the schema is missing. They may simply mean org-specific data has not been inserted yet.

## Known Gaps And Transitional Areas

- There is no RLS yet.
- The `users` table is not yet linked to `auth.users`.
- `public` still hosts all business tables even though direct browser roles are revoked.
- `AUM.id_run` is not linked to `ingestion_runs`.
- The `risk` API reads tables that are absent from committed migrations.
- Frontend requests still pass `id_org` explicitly instead of resolving tenant identity from auth.
- The backend route surface is ahead of the auth model.

## How Claude Should Reason About Future Changes

If proposing schema changes, Claude should follow these rules:

1. Treat `supabase/migrations/` as append-only canonical history.
2. Preserve the backend-first architecture. Do not reintroduce direct browser access to business tables.
3. Keep `id_org` on any new tenant-scoped business table.
4. Prefer composite tenant-aware foreign keys such as `(id_org, id_f)` rather than plain foreign keys when the child table is org-scoped.
5. For new trade families, follow the existing aggregate pattern instead of overloading `trade_disc`.
6. For new reporting datasets, follow the existing header-plus-rows pattern and register the dataset in backend catalog code.
7. Add pgTAP tests when introducing new uniqueness rules, cascade behavior, or security constraints.
8. Treat `risk` as non-canonical until proper migrations exist.

## Short Mental Model

The safest high-level summary is:

- Aegis is currently a backend-first, tenant-aware Postgres schema.
- `organisation` is the main tenancy boundary.
- DISC trade booking is the most mature business flow.
- Reporting is modeled as snapshot headers plus row tables.
- Intraday reporting hangs off `ingestion_runs`.
- SIMM and AUM are daily families with their own semantics.
- Security is currently implemented by revoking browser-style access, not by RLS.
