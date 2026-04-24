# Aegis - Current Project Structure and Service Needs

Date: 2026-04-20

## Purpose

This document describes the project structure and current runtime shape of Aegis based on the codebase and schema currently present in the repository.

This analysis is intentionally derived from:

- `src/frontend/`
- `src/backend/`
- `supabase/migrations/`
- `supabase/tests/`

It does not rely on the project's existing markdown analysis files.

## Executive Summary

Aegis is currently a backend-first web application with:

- one React/Vite frontend
- one FastAPI backend
- one shared Postgres database managed through Supabase migrations

The codebase is not currently an SOA or microservices system. It is a modular monolith with clear internal layers:

- API layer
- domain/service layer
- persistence adapters
- database schema migrations

The database is already modeled as multi-tenant through `id_org`, but runtime tenant security is not yet complete because:

- the frontend still sends `id_org`
- the backend currently trusts request-level tenant inputs
- MSAL wiring is present only as commented placeholders
- there is no active JWT validation path in the backend
- there is no RLS policy layer in the committed migrations

The two additional needs raised for the near future are:

1. Microsoft Entra / MSAL-based authentication and tenant resolution
2. an automatic email sending application or worker

The recommended direction is:

- keep the main business backend as a modular monolith
- add a proper identity/authz module inside the backend
- add a separate email worker or notification service if asynchronous delivery is needed
- do not introduce choreography or an orchestrator yet

## Current Versions

### Backend

File: `src/backend/pyproject.toml`

- package name: `aegis-backend`
- version: `0.1.0`
- Python: `>=3.11`
- main framework: `FastAPI`
- database driver: `psycopg`

### Frontend

File: `src/frontend/package.json`

- package name: `vite-react-typescript-starter`
- version: `0.0.0`
- framework: `React 19`
- router: `react-router-dom`
- charts: `plotly.js`, `recharts`
- state: `zustand`
- build tool: `Vite 7`

### Database / Schema State

Canonical schema history currently comes from `supabase/migrations/`.

Latest committed migration in the repo:

- `20260414000200_add_aum_snapshots.sql`

Security hardening migration exists:

- `20260410001000_lock_down_public_access_until_rls.sql`

But there are currently no committed `RLS` policies or `CREATE POLICY` statements in the migration history.

## Current Repository Structure

```text
aegis-new/
  docs/
    current-project-structure-and-service-needs.md
    database-supabase-backend-report.md
    database-ai-reference.md
    project-state-ai-brief.md

  src/
    frontend/
      package.json
      package-lock.json
      vite.config.ts
      eslint.config.js
      tsconfig.json
      tsconfig.app.json
      tsconfig.node.json
      index.html
      public/
        favicon.svg
        icons.svg
        heroics_aegis_logo*.png
        fonts/
      src/
        App.tsx
        App.css
        main.tsx
        authConfig.ts
        index.css
        assets/
        components/
          Sidebar.tsx
          TopNav.tsx
          ThemeToggle.tsx
          trading/
            ControlsDashboard.tsx
            DataViewer.tsx
            RiskDashboard.tsx
            TradeBooker.tsx
            TradeChecker.tsx
            TradeRecap.tsx
        config/
          runtime.ts
        lib/
          backendClient.ts
        pages/
          LoginPage.tsx
          PlaceholderPage.tsx
          TradingDashboard.tsx
        services/
          recapService.ts
          referenceService.ts
          riskService.ts
          systemService.ts
          tradeService.ts
        store/
          appStore.ts
          themeStore.ts
        types/
          reference.ts
          trades.ts

    backend/
      main.py
      pyproject.toml
      .env.example
      app/
        main.py
        api/
          dependencies.py
          errors.py
          router.py
          v1/
            router.py
            routes/
              data_snapshots.py
              health.py
              reference.py
              risk.py
              trades.py
        bootstrap/
          container.py
        core/
          config.py
          logging.py
        domain/
          shared/
            errors.py
          reference/
            entities.py
            repository.py
            schemas.py
            service.py
          trades/
            entities.py
            enums.py
            repository.py
            schemas.py
            service.py
          data_snapshots/
            catalog.py
            entities.py
            enums.py
            repository.py
            schemas.py
            service.py
        infrastructure/
          persistence/
            memory/
              trade_store.py
              reference_store.py
              data_snapshot_store.py
            postgres/
              base.py
              trades.py
              reference.py
              data_snapshots.py
      tests/
        __init__.py

  supabase/
    config.toml
    seed.sql
    README.md
    migrations/
      20260409020000_init_shared_reference.sql
      20260409020100_init_authz_reference.sql
      20260409020200_init_trade_core.sql
      20260409020300_init_reporting_snapshots.sql
      20260410000100_add_ingestion_runs.sql
      20260410001000_lock_down_public_access_until_rls.sql
      20260414000100_harden_schema_coherence.sql
      20260414000200_add_aum_snapshots.sql
    tests/
      001_security_lockdown.sql
      002_reporting_snapshot_batches.sql
      003_trade_disc_leg_relations.sql
      004_schema_coherence_hardening.sql
    drafts/
      authz-reference-draft.sql
      core-schema-draft.sql
      foundation-migration-order.md
      reference-shared-draft.sql
    functions/
      README.md
```

## Current Runtime Structure

## 1. Frontend

The frontend is a single React application under `src/frontend/`.

Its role today is:

- render the UI
- call backend HTTP endpoints
- manage local UI state
- pass tenant-scoped parameters such as `id_org` and `id_f`

Important technical observations from code:

- all HTTP calls go through `src/frontend/src/lib/backendClient.ts`
- this client uses plain `fetch`
- no `Authorization` header is attached today
- the backend base URL comes from `VITE_BACKEND_API_URL`
- the default tenant comes from `VITE_DEFAULT_ORG_ID`

That means the frontend currently behaves as a thin client for data access, but it still participates in tenant selection.

### Frontend module breakdown

#### `src/frontend/src/config/`

- `runtime.ts`
  Holds runtime environment values such as backend URL and default org ID.

#### `src/frontend/src/lib/`

- `backendClient.ts`
  Shared HTTP utility for `GET` and `POST` requests.

#### `src/frontend/src/services/`

- `tradeService.ts`
  Wraps trade endpoints.
- `referenceService.ts`
  Wraps reference-data endpoints.
- `riskService.ts`
  Wraps risk endpoints.
- `systemService.ts`
  Wraps system/health-like calls.
- `recapService.ts`
  Calls recap endpoints that are not fully backed by the current backend.

#### `src/frontend/src/components/trading/`

Contains screen-level trading widgets:

- booking
- trade viewing
- risk controls display
- recap UI
- placeholder trade checker

#### `src/frontend/src/store/`

Contains UI state:

- selected fund
- theme mode

### Current auth state in frontend

MSAL-related files exist but are not active:

- `src/frontend/src/authConfig.ts`
- commented imports in `src/frontend/src/main.tsx`
- commented imports in `src/frontend/src/App.tsx`

This means the current frontend does not yet authenticate users through Microsoft Entra in runtime.

## 2. Backend

The backend is a single FastAPI application under `src/backend/`.

Its role today is:

- expose API routes
- implement business services
- connect to either in-memory persistence or Postgres
- enforce some business rules at service level

### Current backend layering

#### `app/main.py`

Creates the FastAPI app and attaches:

- settings
- dependency container
- CORS middleware
- routed API tree

#### `app/api/`

HTTP layer only.

Current route groups:

- `system`
- `reference`
- `risk`
- `trades`
- `data snapshots`

#### `app/bootstrap/`

Dependency assembly.

`container.py` decides whether the app uses:

- in-memory stores
- Postgres adapters

#### `app/core/`

Cross-cutting infrastructure:

- environment/config parsing
- logging

#### `app/domain/`

Business modules split by domain:

- `reference`
- `trades`
- `data_snapshots`
- `shared`

Each domain generally contains:

- entities
- repository interfaces
- schemas
- service logic

#### `app/infrastructure/persistence/`

Concrete adapters:

- `memory/`
- `postgres/`

This is a clean sign of an internal service layer with adapter-based persistence, but still inside one deployable backend.

### Current backend characteristics

- one process
- one API surface
- one dependency container
- one shared DB connection target
- no internal service-to-service HTTP calls
- no message broker
- no background worker in repo

So the backend is modular, but not distributed.

## 3. Database

The database layer lives under `supabase/`.

It is the canonical place for:

- schema migrations
- seed data
- database tests
- future Supabase-specific features

### Database structure by concern

#### `supabase/migrations/`

Official schema history.

Main groups of tables visible from the SQL:

- shared reference data
- authz and tenant reference tables
- trading core tables
- reporting snapshot tables
- security and coherence hardening

#### `supabase/tests/`

pgTAP tests for:

- schema lockdown
- snapshot batch relations
- trade DISC leg integrity
- hardening/coherence rules

#### `supabase/drafts/`

Work-in-progress SQL, not the production history.

#### `supabase/functions/`

Currently only a placeholder. There is no implemented edge-function-based business logic.

## Current Architecture Assessment

## 1. What the codebase is today

The current project is best described as:

- a modular monolith
- with a 3-tier runtime shape
- using a shared Postgres database

Practical runtime view:

```text
Browser -> FastAPI API -> Postgres
```

Supabase currently acts primarily as:

- local Postgres stack
- migration/test host
- future platform capability

It is not currently acting as the main browser-side application API.

## 2. What the codebase is not today

It is not currently:

- a microservices architecture
- a true SOA platform
- an event-driven system
- an orchestrated workflow system
- a choreography-based system

There is no evidence in runtime code of:

- service-to-service contracts between independent business services
- separate bounded services with separate deployments
- broker-based eventing
- workflow orchestration engines

## Multi-Tenancy: Current State

## 1. What is already good

The database model is already tenant-aware.

Tenant boundary:

- `organisation`
- technical key: `id_org`

This is visible directly in the migrations:

- `organisations`
- `users`
- `funds`
- `books`
- `counterparties`
- trade tables
- snapshot tables

Many relations repeat `id_org` in foreign keys, which is a strong design choice for shared-schema multi-tenancy.

Examples:

- `(id_org, id_f)`
- `(id_org, id_user)`
- `(id_org, id_book)`
- `(id_org, id_ctpy)`

This is the correct shape for a shared database serving 2-3 tenants and can remain viable well beyond that.

## 2. What is not finished

The runtime authorization model is not complete.

Current issues:

- API routes accept `id_org` from query params
- create payloads accept `id_org` inside the body
- trade creation payloads also accept `booked_by`
- frontend still supplies default tenant context from environment
- backend has no active auth dependency chain
- frontend has no active MSAL session provider
- frontend does not send bearer tokens
- database browser roles are locked down, but user-level authz is not enforced through RLS

This means the system is tenant-modeled, but not yet tenant-secure at runtime.

## Need 1: Microsoft Entra / MSAL Authentication

## Business need

The project needs Microsoft Entra / MSAL-based authentication so that:

- users sign in with corporate identity
- the backend knows who the user is
- tenant access is resolved server-side
- business operations stop trusting client-supplied identity/tenant values

## What this should mean architecturally

This should not automatically become a separate microservice.

The cleaner design is:

```text
Frontend -> Microsoft Entra via MSAL
Frontend -> Backend with bearer token
Backend -> validates token
Backend -> resolves app user via entra_oid
Backend -> resolves allowed organisations/funds/roles
```

## Recommended implementation shape

### Frontend

- enable MSAL in `main.tsx`
- define real config in `authConfig.ts`
- acquire access token after login
- attach `Authorization: Bearer <token>` in `backendClient.ts`

### Backend

Add an internal identity/authz module, not a separate platform service first.

Suggested responsibilities:

- token validation
- extraction of user `oid`
- lookup of `users.entra_oid`
- loading of user access roles and permitted organisations
- rejection of unauthorized tenant access

### Data contract changes required

Once auth is active, the client should stop being the source of truth for:

- `id_org`
- `booked_by`

Instead:

- the backend derives the caller identity from the token
- the backend resolves allowed tenants
- the backend sets actor fields internally

## Why this does not need a separate "auth microservice" yet

At this stage, a separate auth microservice would mostly add:

- another deployment unit
- more network hops
- duplicate error paths
- more operational burden

without solving the core issue, which is application authorization.

The identity provider already exists outside your system:

- Microsoft Entra ID

Your backend mainly needs to become a proper relying party and authorization boundary.

## Need 2: Automatic Email Sending Application

## Business need

The project also needs an application or service that sends automatic emails.

This is materially different from the main API because it is:

- asynchronous
- retry-oriented
- schedule-oriented
- operationally different from request/response business APIs

## This is a good candidate for separation

Unlike auth, email delivery is a reasonable candidate for a separate worker or notification service.

Why:

- it can run independently of user HTTP traffic
- it benefits from retries and dead-letter handling
- it may need throttling or provider-specific handling
- it should not block interactive API requests

## Recommended shape

Short term:

```text
API writes email job -> email worker sends email
```

Prefer an outbox/job-table pattern first:

- `notification_jobs` or `email_jobs` table
- API inserts a job in the same transaction as the business event when needed
- worker polls pending jobs
- worker sends email using Microsoft Graph or another provider
- worker records success, failure, and retry count

## Why this is better than choreography right now

At current scale, choreography would be unnecessary complexity.

You do not yet have:

- many autonomous services
- many independent event consumers
- long-running distributed workflows
- compensating transactions across services

That means a simple worker pattern is the better fit.

## Do You Need a Service Layer?

Yes, but the right interpretation is important.

### You already have an internal service layer

The backend already contains service-layer code in:

- `src/backend/app/domain/trades/service.py`
- `src/backend/app/domain/reference/service.py`
- `src/backend/app/domain/data_snapshots/service.py`

This is good and should be extended.

### What you need next

You likely need more business modules, not a full SOA split:

- `identity`
- `authorization`
- `notifications`
- possibly `jobs`

Suggested internal module additions:

```text
src/backend/app/domain/
  identity/
  authorization/
  notifications/
```

## Do You Need Choreography or an Orchestrator?

Not yet.

### You do not need choreography now because

- there are not multiple autonomous business services reacting to domain events
- there is no event mesh or broker in place
- the main problem to solve is still authentication and request-side authorization

### You do not need a workflow orchestrator now because

- there are no long-running multi-service sagas
- there is no evidence of distributed transactions
- your current future asynchronous need is email sending, which is much simpler than workflow orchestration

### What you do need instead

- clear backend service boundaries inside the monolith
- a token validation/authz layer
- a notification job table
- an email worker

## Recommended Target Architecture

For the current stage of Aegis, the recommended target is:

```text
Frontend (React + MSAL)
  -> Backend API (FastAPI modular monolith)
      -> Postgres / Supabase
      -> Email jobs table

Email worker
  -> reads jobs
  -> sends emails through Microsoft Graph / Outlook
```

### Responsibilities

#### Frontend

- authenticate user with Entra/MSAL
- present UI
- call backend with bearer token
- never be source of truth for authorization

#### Backend API

- validate caller identity
- resolve allowed tenant and fund access
- apply business rules
- expose business endpoints
- enqueue notification jobs

#### Email worker

- handle asynchronous delivery
- implement retries and error tracking
- isolate email-provider concerns from the API

## Suggested Future Repository Structure

One reasonable next-step structure would be:

```text
aegis-new/
  src/
    frontend/
    backend/
      app/
        api/
        bootstrap/
        core/
        domain/
          identity/
          authorization/
          notifications/
          reference/
          trades/
          data_snapshots/
        infrastructure/
          persistence/
          identity/
          mail/
    email_worker/
      pyproject.toml
      worker/
        main.py
        jobs.py
        mail_provider.py
        retry_policy.py
  supabase/
    migrations/
      ...existing...
      <future>_add_notification_jobs.sql
```

## Recommended Near-Term Roadmap

## Phase 1 - Secure the current monolith

- enable MSAL in the frontend
- send bearer tokens to backend
- add backend token validation
- map token `oid` to `users.entra_oid`
- stop trusting client-supplied `id_org`
- stop trusting client-supplied `booked_by`

## Phase 2 - Formalize authorization

- add backend authorization services
- resolve allowed orgs/funds/roles server-side
- add tenant-aware request context
- optionally add DB-side RLS later as defense in depth

## Phase 3 - Add async notifications

- create `email_jobs` or `notification_jobs`
- add a worker
- integrate Microsoft Graph or chosen provider
- add retry and status tracking

## Phase 4 - Re-evaluate service extraction

Only after the above is stable should you decide whether:

- the email worker remains just a worker
- notifications become a standalone service
- identity remains internal or becomes externalized for multiple applications

## Final Recommendation

The current Aegis codebase already has the right foundations for:

- a backend-first architecture
- shared-schema multi-tenancy
- a service layer inside the backend

The next good move is not a broad jump to SOA.

The next good move is:

1. finish authentication and authorization correctly
2. keep the main business API as a modular monolith
3. add a separate email worker for asynchronous notification delivery

That gives you:

- lower operational complexity
- better security
- clearer responsibility boundaries
- room to split later only where it is justified

## Short Verdict

- Current architecture: modular monolith
- Current tenant model: good in schema, incomplete in runtime security
- Need for internal service layer: yes
- Need for full SOA now: no
- Need for separate email worker/service: yes, likely
- Need for choreography/orchestrator now: no
