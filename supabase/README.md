# Supabase Layout

This directory is the Supabase source of truth for local development and schema evolution.

## Structure

- `config.toml`: local Supabase CLI configuration. Safe to commit if it contains no secrets.
- `migrations/`: versioned schema changes. This is the canonical database history.
- `seed.sql`: local seed data only. Keep it non-sensitive.
- `tests/`: SQL tests for RLS, permissions, and schema behavior.
- `functions/`: Edge Functions, only if needed later.
- `drafts/`: temporary SQL working files that are not yet ready to become migrations.

## Rules

- Do not put secrets in this directory unless they are loaded through `env(...)`.
- Do not use ad hoc `tables.sql` files as the long-term schema source.
- Move drafts into `migrations/` once they are reviewed and stable.

## Current Security Posture

- The `public` schema is currently locked down to backend / `service_role` access.
- Direct `anon` / `authenticated` access is intentionally revoked until a dedicated RLS migration is added.
- If you need direct Supabase client access later, add the auth mapping and RLS policies first, then relax grants deliberately.

## Snapshot Model

- `ingestion_runs` is the parent record for intraday reporting snapshot batches.
- `id_run` is auto-generated on `ingestion_runs`; create the parent row first, then reuse the returned `id_run` in all intraday child snapshot headers.
- `simm_snapshots` stays separate from intraday snapshot linkage. Its `id_run` is a daily source-side load reference, not a FK to `ingestion_runs`.
