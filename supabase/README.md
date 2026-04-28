# Aegis Supabase

## Overview

This directory is the source of truth for the local database used by Aegis.

It contains:

- Supabase CLI configuration
- versioned SQL migrations
- local seed data
- pgTAP database tests
- draft SQL that has not yet been promoted to migrations

In the current architecture, the frontend does not use Supabase directly for core trading data. The backend connects to the Postgres instance managed by the local Supabase stack.

## Local Service Ports

The local ports are defined in `supabase/config.toml`.

Important defaults:

- API gateway: `http://127.0.0.1:54321`
- Postgres: `127.0.0.1:54322`
- Studio: `http://127.0.0.1:54323`
- Inbucket: `http://127.0.0.1:54324`

Direct backend database URL:

```text
postgresql://postgres:<local-password>@127.0.0.1:54322/postgres
```

## Directory Structure

```text
supabase/
  config.toml       Local Supabase CLI configuration
  migrations/       Canonical schema history
  seed.sql          Local non-sensitive seed data
  tests/            pgTAP regression tests
  drafts/           Work-in-progress SQL not ready for migration history
  functions/        Edge Functions, if needed later
```

## How This Fits Into The Project

Current expected data flow:

```text
Frontend -> Backend -> Postgres (inside the local Supabase stack)
```

Implications:

- the browser does not need `SUPABASE_URL` or an anon key for the main application flows
- the backend should use `AEGIS_DATABASE_URL` to connect directly to Postgres
- Supabase Studio remains useful for inspection, auth work, and future storage or function features

## Local Workflow

Start the local Supabase stack:

```bash
supabase start
```

Reset the database from migrations and seed data:

```bash
supabase db reset
```

Lint the SQL schema:

```bash
supabase db lint
```

Run database tests:

```bash
supabase test db
```

## Migrations

The `migrations/` directory is the official database history.

Rules:

- every migration file must match the Supabase timestamp naming pattern: `<timestamp>_name.sql`
- migrations should be append-only
- reviewed schema changes belong in `migrations/`
- experimental SQL belongs in `drafts/` until it is ready

Examples:

- `20260409020000_init_shared_reference.sql`
- `20260410000100_add_ingestion_runs.sql`
- `20260414000200_add_aum_snapshots.sql`

Logical placement notes:

- `currencies`, `asset_classes`, `countries`, `cities`, `fx_rates`, and `quotes` are global shared reference tables created in `20260409020000_init_shared_reference.sql`.
- `20260420000100_add_login_quotes.sql` only seeds initial login quotes.
- `aum_snapshots` and `aum_rows` are part of the reporting snapshot layer, even though they were introduced later in `20260414000200_add_aum_snapshots.sql`.

## Seed Data

`seed.sql` is for local, non-sensitive data only.

At the moment, it seeds shared reference data such as:

- `currencies`
- `asset_classes`
- initial `quotes`

It does not fully seed organisation-specific business entities such as funds, books, trade labels, or counterparties.

That means:

- the backend can connect successfully after a reset
- reference endpoints like asset classes and currencies can return data immediately
- some organisation-scoped endpoints may still return empty arrays until tenant data is inserted

## Security Posture

The current database setup is intentionally conservative.

- the `public` schema is locked down for backend-oriented access
- direct `anon` and `authenticated` browser access is not part of the current runtime design
- row-level security and auth-facing access can be added later, but should be introduced deliberately

## Snapshot Schema Notes

The reporting model is snapshot-oriented.

Important points:

- `ingestion_runs` is the parent record for intraday reporting loads
- intraday snapshot headers can link back to `ingestion_runs`
- `simm_snapshots` keeps separate semantics and does not behave like the intraday snapshot families
- `aum_snapshots` is daily reporting data like SIMM and does not link to `ingestion_runs`

This structure supports datasets such as AUM, SIMM, expiries, leverages, and related reporting tables.

## Common Troubleshooting

### `supabase db reset` skips a file

Supabase only executes files that match the migration naming convention.

Example:

- `README.md` inside `migrations/` is expected to be skipped

### `supabase db reset` fails with a syntax error at the first character

Check for an invisible UTF-8 BOM at the start of a SQL file. PostgreSQL can fail immediately if the migration begins with that hidden character.

### `supabase db reset` ends with a 502 during container restart

If migrations and seed statements already finished before the `502`, the schema reset often completed and the failure happened while the local gateway was restarting.

Recommended next checks:

1. wait a few seconds
2. run `supabase status`
3. retry the command once the stack is healthy

### Reference endpoints are empty after a successful reset

This usually means the shared seed loaded correctly, but organisation-scoped business rows were not inserted yet.

## Recommended Collaboration Rules

- keep production secrets out of committed SQL and config files
- prefer migrations over ad hoc schema dumps
- keep seed data safe to replay
- add pgTAP tests when introducing critical constraints, grants, or security changes
- promote files from `drafts/` to `migrations/` only after review
