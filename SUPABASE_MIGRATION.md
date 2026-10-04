# CyberSathi Supabase migration

## Current status

The application has been prepared for a PostgreSQL provider change, but the
production cutover is **not complete**. The live frontend still uses the
currently configured production API, and the current API deployment must not
be removed until a replacement API has been deployed and verified.

The existing FastAPI service contains the authentication, authorization,
analysis, quiz, incident, chat, and admin business logic. Supabase can host
the PostgreSQL database used by that service, but it does not run this
arbitrary FastAPI application directly. The supported target architecture is:

```text
GitHub Pages React frontend
        |
        v
FastAPI API on a non-Render production host
        |
        v
Supabase PostgreSQL
```

The existing custom JWT authentication is retained during the database
migration. Migrating to Supabase Auth would require a separate user/session
migration and is intentionally not part of this safe cutover.

## Why the code is compatible

- SQLAlchemy already receives the database connection through `DATABASE_URL`.
- Alembic already owns the schema history; the current head is
  `20260822_0009`.
- Supabase PostgreSQL is PostgreSQL-compatible, so the existing models and
  migrations remain the source of truth.
- The browser API endpoint is already configured through
  `VITE_API_BASE_URL`; no database or Supabase service-role key belongs in the
  frontend.
- CORS is configured through `CORS_ORIGINS`/`FRONTEND_ORIGINS` and rejects
  wildcard origins.

## Required external setup

The following actions require provider dashboard access and cannot be
completed safely from this repository alone:

1. Create or select the Supabase project owned by the project owner.
2. Provision a non-Render production host for the FastAPI service. Supabase
   Edge Functions are not a drop-in runtime for this application.
3. Obtain the Supabase PostgreSQL connection string privately from Supabase.
   Never put it in Git, frontend variables, or chat.
4. Configure the replacement API host with the same application secrets and
   `DATABASE_URL`.
5. Configure a release/pre-deploy command on the replacement API host:

   ```text
   alembic upgrade head
   ```

6. Set the frontend deployment variable `VITE_API_BASE_URL` to the verified
   replacement API base path, for example `<NEW_API_ORIGIN>/api/v1`. Do not
   replace it with an unverified or invented URL.

## New database with no legacy data

Use this path only when the old database has been backed up or there is no
legacy data to preserve:

```powershell
cd backend
python -m alembic upgrade head
python -m alembic current
python -m alembic heads
```

`current` must report `20260822_0009`, matching `heads`. The migration command
must run against the private Supabase `DATABASE_URL`, not a local SQLite file.

## Data-preserving migration

If the old PostgreSQL database is reachable, take an encrypted backup before
cutover and restore it into a non-production Supabase project first. Do not
run destructive SQL against either database.

The exact `pg_dump`/`pg_restore` commands depend on the provider connection
details and must be run from a controlled machine without placing passwords in
command history. After restore, validate the schema and run only the pending
Alembic migrations. If the old Render database is unavailable, the existing
records cannot be recovered by code changes; obtain a provider backup or
restore source before creating a replacement database.

## Cutover checklist

- [ ] Supabase project and billing/plan confirmed.
- [ ] Old database backup or explicit decision that the replacement is empty.
- [ ] Supabase database connection tested privately.
- [ ] Alembic reaches `20260822_0009`.
- [ ] FastAPI replacement host is live over HTTPS.
- [ ] `GET /health` and `GET /api/v1/health` return successful JSON.
- [ ] `DATABASE_URL` is present only in the replacement API secret store.
- [ ] `CORS_ORIGINS=https://kszarodiya-debug.github.io` is configured.
- [ ] Synthetic registration, login, logout, protected route, and admin
      authorization tests pass against the replacement API.
- [ ] `VITE_API_BASE_URL` is changed to the verified replacement API URL.
- [ ] GitHub Pages build and deployment succeed.
- [ ] Live browser tests pass from the GitHub Pages site.
- [ ] Only after all checks pass, remove the old Render service and references
      that are no longer relevant.

## Secret handling

Keep these values only in provider-managed secret storage:

- `DATABASE_URL`
- `JWT_SECRET`
- `AI_API_KEY`
- `ADMIN_INITIAL_PASSWORD`

Only the public API origin belongs in the GitHub Pages build configuration.
Never use a Supabase service-role key in React or a GitHub Pages variable.
