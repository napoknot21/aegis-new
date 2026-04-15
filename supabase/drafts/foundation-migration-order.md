# SQL Migration Order

This note describes the migration order used to convert the validated drafts
into the official schema history.

## Missing Foundation Tables

The current draft still depends on these tables:

- `currencies`
- `asset_classes`
- `organisations`
- `offices`
- `departments`
- `office_departments`
- `users`
- `ranks`
- `access_roles`

It also references business concepts that should probably exist before or alongside later migrations:

- `user_offices`
- `user_departments`
- `user_ranks`
- `user_access_roles`
- `ingestion_runs` or `import_runs`

## Recommended Migration Order

1. `20260409020000_init_shared_reference.sql`

- `currencies`
- `asset_classes`

2. `20260409020100_init_authz_reference.sql`

- `organisations`
- `offices`
- `departments`
- `office_departments`

- `users`
- `ranks`
- `access_roles`
- `user_offices`
- `user_departments`
- `user_ranks`
- `user_access_roles`
- fund and organisation scoping tables

3. `20260409020200_init_trade_core.sql`

- `funds`
- `fund_office_access`
- `banks`
- `counterparties`
- `books`
- `trade_types`
- `trade_disc_labels`
- `trade_spe`
- `trades`
- `trade_disc`
- trade child tables

4. `20260409020300_init_simm_and_expiries.sql`

- `simm_snapshots`
- `simm_snapshot_rows`
- `expiries_snapshots`
- `expiries`

5. `enable_rls.sql`

- enable RLS
- create policies
- restrict grants

6. `audit_and_helpers.sql`

- audit log tables
- helper views
- privileged functions if really needed

## Why This Order

- reference tables must exist before foreign keys
- authz must exist before RLS can be designed properly
- trade tables should be stabilized before building APIs on top of them
- reporting and ingestion tables are easier once the core dimensions are fixed
