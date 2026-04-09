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
