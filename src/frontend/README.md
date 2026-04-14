# Aegis Frontend

## Overview

This package contains the Aegis web application built with React, TypeScript, and Vite.

The frontend is now designed to talk to the Aegis backend only. It does not use `@supabase/supabase-js` or direct browser-side Supabase queries for the main application flows.

Current runtime flow:

1. The browser calls the shared HTTP client in `src/lib/backendClient.ts`.
2. The client targets the FastAPI backend under `VITE_BACKEND_API_URL`.
3. The backend reads from either the in-memory adapters or the local Supabase/Postgres database.

## Tech Stack

- React 19
- TypeScript
- Vite
- Zustand for lightweight UI state
- Plotly and Recharts for visual components
- Lucide icons

## Directory Structure

```text
src/
  components/        Reusable UI blocks and trading screens
  config/            Runtime configuration derived from Vite env vars
  lib/               Shared infrastructure such as the backend HTTP client
  pages/             Route-level screens
  services/          Backend-facing API wrappers
  store/             Zustand stores for UI state
  types/             Shared frontend types
```

## Environment Variables

Create `src/frontend/.env` from `.env.example` and set:

```env
VITE_BACKEND_API_URL=http://localhost:8000/api/v1
VITE_DEFAULT_ORG_ID=1
```

Meaning:

- `VITE_BACKEND_API_URL`: base URL used by the shared backend client.
- `VITE_DEFAULT_ORG_ID`: default organisation id sent by the frontend when the UI does not yet expose explicit organisation switching.

## Local Development

Install and run the frontend:

```bash
cd src/frontend
npm install
npm run dev
```

Build for production:

```bash
cd src/frontend
npm run build
```

The backend is expected at `http://localhost:8000/api/v1` unless you override `VITE_BACKEND_API_URL`.

## Backend Integrations By Screen

### Login Page

`src/pages/LoginPage.tsx` calls:

- `GET /system/login-quote`

This route supplies the quote block shown on the login screen.

### Sidebar

`src/components/Sidebar.tsx` calls:

- `GET /reference/funds?id_org=...`

The selected fund is stored in Zustand and reused by the trading views.

### Trade Booker

`src/components/trading/TradeBooker.tsx` calls:

- `GET /reference/asset-classes`
- `GET /reference/currencies`
- `GET /reference/books?id_org=...`
- `GET /reference/counterparties?id_org=...`
- `GET /trades/labels?id_org=...`
- `POST /trades/disc`

This screen is the main example of the new architecture: the form loads all reference data from the backend and submits a typed DISC payload to the backend trade route.

### Trade Viewer

`src/components/trading/DataViewer.tsx` calls:

- `GET /trades?id_org=...`

It displays trade summaries returned by the backend rather than querying database tables directly from the browser.

### Controls Dashboard

`src/components/trading/ControlsDashboard.tsx` calls:

- `GET /risk/controls?id_org=...&id_f=...`

The threshold definitions come from the backend. The historical chart values and change metrics shown on the page are still mocked in the component until a time-series source is added.

### Trade Recap

`src/components/trading/TradeRecap.tsx` now uses the shared service layer instead of hardcoded URLs.

It targets:

- `GET /recap/run`
- `POST /recap/book`

Important note:

The recap service path is frontend-wired, but the backend recap API is not implemented yet. The screen will therefore show a clear error if you try to run it against the current backend.

### Trade Checker

`src/components/trading/TradeChecker.tsx` is still a static placeholder. It does not call the backend yet.

## Shared HTTP Client

All backend calls should go through `src/lib/backendClient.ts`.

Why this matters:

- the backend base URL is configured in one place
- query-string construction is consistent
- JSON error handling is consistent
- components stay focused on UI logic instead of low-level `fetch` handling

When you add a new screen or data source, prefer this pattern:

1. Create or extend a file in `src/services/`.
2. Use `apiGet` or `apiPost`.
3. Keep raw `fetch` usage inside `backendClient.ts` only.

## State Management

Two small stores currently exist:

- `useAppStore` for selected fund and global date
- `useThemeStore` for the theme mode

The selected fund is especially important because several backend calls depend on `id_f`.

## Current Limitations

- `VITE_DEFAULT_ORG_ID` is still the frontend source for `id_org`.
- `TradeChecker` is not backend-connected yet.
- `TradeRecap` is wired through the frontend service layer, but the backend recap endpoints do not exist yet.
- `ControlsDashboard` mixes real threshold metadata with mocked chart data.
- The production build currently emits a large bundle warning. The app still builds successfully, but chunking can be improved later.

## Verification Notes

A clean integration check for this package is:

```bash
cd src/frontend
npm run build
```

Useful spot checks once the backend is running:

- open the login page and verify the quote loads
- confirm the sidebar fund selector loads from the backend
- confirm the trade booker dropdowns load without any direct Supabase client configuration
- confirm the trade viewer table loads from `GET /trades`
