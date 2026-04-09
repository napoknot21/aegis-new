# SQL Migration Order

This note describes the minimum migration order needed before
`core-schema-draft.sql` can become part of the official schema history.

## Missing Foundation Tables

The current draft still depends on these tables:

- `organisations`
- `currencies`
- `offices`
- `asset_classes`
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

1. `init_reference_data.sql`

- `organisations`
- `currencies`
- `offices`
- `asset_classes`
- `departments`
- `office_departments`

2. `init_authz.sql`

- `users`
- `ranks`
- `access_roles`
- `user_offices`
- `user_departments`
- `user_ranks`
- `user_access_roles`
- fund and organisation scoping tables

3. `init_trade_core.sql`

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

4. `init_simm_and_expiries.sql`

- `simm_snapshots`
- `simm_rows`
- `expiries_snapshots`
- `expiries_rows`

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
