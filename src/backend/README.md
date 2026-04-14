# Aegis Backend

This backend has been rebuilt as a service-oriented FastAPI application.

## Principles

- one API process for now, with clear domain boundaries
- modular enough to split into microservices later if needed
- no domain logic inside route handlers
- persistence behind interfaces so Postgres/Supabase can replace the in-memory adapter cleanly
- first-class support for the DISC trade creation flow
- snapshot-oriented data domain for SIMM, AUM, expiries, leverages, and related reporting families

## Layout

```text
app/
  api/              HTTP layer only
  bootstrap/        container wiring
  core/             settings and logging
  domain/           business models and application services
  infrastructure/   adapters (currently in-memory persistence)
legacy_pre_refactor_20260414/
  previous backend snapshot
```

## First implemented domains

- `POST /api/v1/trades/disc`
- `GET /api/v1/trades`
- `GET /api/v1/trades/disc/{id_spe}`
- `GET /api/v1/trades/types`
- `GET /api/v1/system/health`
- `GET /api/v1/data/datasets`
- `GET /api/v1/data/{dataset}/snapshots`
- `GET /api/v1/data/{dataset}/snapshots/{snapshot_id}`
- `POST /api/v1/data/{dataset}/snapshots`

## Data snapshots catalog

The backend now exposes a generic snapshot domain for:

- `AUM`
- `SIMM`
- `EXPIRIES`
- `NAV_ESTIMATED`
- `LEVERAGES`
- `LEVERAGES_PER_TRADE`
- `LEVERAGES_PER_UNDERLYING`
- `LONG_SHORT_DELTA`
- `COUNTERPARTY_CONCENTRATION`

This is intentionally generic for now so the future ICE `libapi` adapter can create daily or intraday snapshots without rewriting the API surface.

## Run later

```bash
uvicorn app.main:app --reload --port 8000
```

or

```bash
python main.py
```
