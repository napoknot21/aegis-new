# Aegis Backend

## Overview

This package contains the Aegis FastAPI service.

Its job is to sit between the frontend and the data layer. The frontend should call this backend, and the backend should own the rules for:

- trade workflows
- reference data access
- reporting snapshot access
- basic system endpoints
- backend-only access to the local Supabase/Postgres database

## Runtime Role

Current runtime flow:

1. The frontend sends HTTP requests to `/api/v1/...`.
2. FastAPI routes dispatch into application services.
3. The container selects a persistence backend.
4. The persistence layer reads from either in-memory stores or Postgres.

The intended production-style path is:

```text
Frontend -> FastAPI backend -> Postgres/Supabase
```

The browser is no longer expected to query Supabase tables directly for the main trading flows.

## Project Structure

```text
app/
  api/              FastAPI routes, dependency wiring, and HTTP error mapping
  bootstrap/        Container construction and adapter selection
  core/             Settings and logging
  domain/           Business entities, schemas, repositories, and services
  infrastructure/   Persistence adapters
main.py             Local development entry point
```

## Persistence Modes

The backend supports three configuration modes through `AEGIS_PERSISTENCE_BACKEND`:

- `memory`: use in-memory stores only
- `postgres`: require a real PostgreSQL connection
- `auto`: use Postgres when `AEGIS_DATABASE_URL` is set, otherwise fall back to memory

This logic is implemented in `app/core/config.py` and `app/bootstrap/container.py`.

## Environment Variables

Create `src/backend/.env` from `.env.example` and set the values you need.

Important variables:

```env
AEGIS_APP_NAME=Aegis Backend
AEGIS_ENVIRONMENT=development
AEGIS_DEBUG=true
AEGIS_API_PREFIX=/api/v1
AEGIS_HOST=0.0.0.0
AEGIS_PORT=8000
AEGIS_ALLOWED_ORIGINS_RAW=http://localhost:5173,http://127.0.0.1:5173
AEGIS_PERSISTENCE_BACKEND=postgres
AEGIS_DATABASE_URL=postgresql://postgres:<local-password>@127.0.0.1:54322/postgres
```

Meaning:

- `AEGIS_ALLOWED_ORIGINS_RAW`: comma-separated CORS allow-list
- `AEGIS_PERSISTENCE_BACKEND`: selects memory, postgres, or auto mode
- `AEGIS_DATABASE_URL`: direct Postgres connection string used by the backend

## Running Locally

Install dependencies and start the API:

```bash
cd src/backend
uv sync
python main.py
```

Interactive documentation is then available at:

- `http://localhost:8000/docs`

Health endpoint:

- `http://localhost:8000/api/v1/system/health`

The health response includes `persistence_backend` so you can confirm whether the service is running in `memory` or `postgres` mode.

## Implemented API Surface

### System

- `GET /api/v1/system/health`
- `GET /api/v1/system/login-quote`

### Reference Data

- `GET /api/v1/reference/asset-classes`
- `GET /api/v1/reference/currencies`
- `GET /api/v1/reference/funds?id_org=...`
- `GET /api/v1/reference/books?id_org=...`
- `GET /api/v1/reference/books?id_org=...&id_f=...`
- `GET /api/v1/reference/counterparties?id_org=...`

Trade labels are intentionally exposed under the trades namespace:

- `GET /api/v1/trades/labels?id_org=...`

### Trades

- `GET /api/v1/trades?id_org=...`
- `GET /api/v1/trades/types?id_org=...`
- `GET /api/v1/trades/disc/{id_spe}?id_org=...`
- `POST /api/v1/trades/disc`

### Reporting Snapshots

- `GET /api/v1/data/datasets`
- `GET /api/v1/data/{dataset}/snapshots?id_org=...`
- `GET /api/v1/data/{dataset}/snapshots/{snapshot_id}?id_org=...`
- `POST /api/v1/data/{dataset}/snapshots`

Supported dataset codes currently include:

- `AUM`
- `SIMM`
- `EXPIRIES`
- `NAV_ESTIMATED`
- `LEVERAGES`
- `LEVERAGES_PER_TRADE`
- `LEVERAGES_PER_UNDERLYING`
- `LONG_SHORT_DELTA`
- `COUNTERPARTY_CONCENTRATION`

Snapshot list filtering supports:

- `id_f`
- `status`
- `is_official`
- `as_of_date`
- `as_of_date_from`
- `as_of_date_to`

### Risk

- `GET /api/v1/risk/controls?id_org=...&id_f=...`

## Architecture Notes

### Route Layer

The route files under `app/api/v1/routes/` should stay thin. They validate HTTP inputs, call the service layer, and return response models.

### Service Layer

The main application services currently are:

- `TradeApplicationService`
- `ReferenceApplicationService`
- `DataSnapshotApplicationService`

These services depend on repository/unit-of-work interfaces rather than concrete database code.

### Persistence Layer

Two adapter families exist:

- `app/infrastructure/persistence/memory/`
- `app/infrastructure/persistence/postgres/`

The Postgres adapters are the bridge to the local Supabase database.

## Current Implementation Status

### Fully Backend-Owned Flows

- trade listing
- DISC trade creation
- reference dropdown data for the trading UI
- snapshot discovery and retrieval
- backend health reporting

### Transitional Areas

- `risk.py` still issues SQL directly instead of going through a dedicated domain service. This is intentional for now, but it is not the final architecture.
- recap endpoints are not implemented yet
- some frontend screens depend on business data that is not seeded by default in the local database

## Local Database Expectations

The local seed currently loads shared reference data such as:

- currencies
- asset classes

It does not fully seed organisation-specific business rows such as:

- organisations
- funds
- books
- users
- counterparties
- trade labels

If those rows are missing, the backend can still start successfully, but some business endpoints may return empty arrays.

## Verification

Useful local checks:

```bash
cd src/backend
python -m compileall app main.py
```

If the database is running, useful HTTP checks include:

- `GET /api/v1/system/health`
- `GET /api/v1/reference/asset-classes`
- `GET /api/v1/reference/currencies`
- `GET /api/v1/trades/labels?id_org=...`
- `GET /api/v1/data/EXPIRIES/snapshots?id_org=...`

## Development Guidance

When adding new backend features:

1. Prefer adding a service method instead of embedding business logic inside routes.
2. Prefer adding typed response models in the domain schema modules.
3. Prefer extending the Postgres adapter behind the existing unit-of-work pattern.
4. Keep the frontend talking to this backend rather than introducing new direct browser-to-database access.
