# CyberSathi deployment

CyberSathi currently uses GitHub Pages for the frontend and has a legacy
Render deployment for the FastAPI API. A Supabase migration is documented in
[SUPABASE_MIGRATION.md](SUPABASE_MIGRATION.md), but it is not complete until a
Supabase PostgreSQL project and a separately hosted FastAPI API have both been
verified. Do not change the live API URL or delete the current deployment
before that verification.

Credentials remain in provider-managed secret storage and are not committed
to this repository.

Live services:

- Frontend: https://kszarodiya-debug.github.io/cybersathi/
- Backend: https://cybersathi-2bao.onrender.com
- Health: https://cybersathi-2bao.onrender.com/api/v1/health
- Repository: https://github.com/kszarodiya-debug/cybersathi

## Required production configuration

Configure secrets through the hosting platform's secret manager or environment settings:

- `APP_ENV=production`
- `DATABASE_URL` for a private PostgreSQL service, preferably with TLS parameters.
- `DATABASE_CONNECT_TIMEOUT_SECONDS=10` to bound failed database connection attempts.
- `RUN_MIGRATIONS_ON_STARTUP=false` for the web service; run `alembic upgrade head` as a separate release step and verify `alembic current`.
- `JWT_SECRET` generated randomly and at least 32 characters long.
- Stable `JWT_ISSUER` and `JWT_AUDIENCE` values.
- `CORS_ORIGINS` containing only the real HTTPS frontend origin(s), with no wildcard. The existing `FRONTEND_ORIGINS` name remains supported for compatibility.
- `VITE_API_BASE_URL` at frontend build time, pointing to the real API base path.
- `AI_API_KEY` only if the assistant is enabled.
- `AI_BASE_URL` using HTTPS in production.
- `ADMIN_EMAIL` and `ADMIN_INITIAL_PASSWORD` only during the private one-time admin bootstrap; the password must be at least 16 characters and must never be committed.

Do not put backend secrets in frontend build variables. Do not commit `.env`, `.env.*`, provider keys, database credentials, access tokens, or generated certificates.

## Database release sequence

1. Provision a private PostgreSQL database and least-privilege application role.
2. Configure `DATABASE_URL` through the secret manager.
3. Run `alembic upgrade head` from the backend image/environment as a separate release step before routing application traffic. Do not use the web process as an unbounded migration runner. If the Render plan cannot provide a release/pre-deploy command, run the command once from an authenticated private Render shell or controlled release environment, then keep `RUN_MIGRATIONS_ON_STARTUP=false`.
4. Run `python -m app.bootstrap_admin` once from a private backend shell/job with `ADMIN_EMAIL` and `ADMIN_INITIAL_PASSWORD` configured. This is the only supported designated-admin provisioning path.
5. Verify the migration head and application health.
6. Encrypt backups and define retention/deletion policies for chat, analysis, incident, and audit data.

The web process exposes liveness independently of migrations. Migration failures are not swallowed: the release command must fail and deployment must be stopped until the database is corrected. Database-dependent API requests will not be considered ready until `alembic current` reports `20260822_0009`.

## Backend release sequence

```powershell
cd backend
pip install -r requirements.txt
python -m pytest -q
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Place the API behind a TLS-terminating reverse proxy or managed HTTPS gateway. Configure request-size limits, upstream timeouts, health checks, access-log redaction, and a shared rate limiter. Do not expose PostgreSQL publicly.

## Frontend release sequence

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run lint
pnpm run test
pnpm run build
```

Publish `frontend/dist/` using the selected static hosting provider. Configure the real API origin at build time through `VITE_API_BASE_URL`. Configure the static host or reverse proxy to provide HTTPS, a restrictive Content Security Policy, clickjacking protection, MIME sniffing protection, and appropriate cache rules for HTML versus hashed assets.

The GitHub Pages workflow sets `VITE_BASE_PATH` for the project site and reads the repository variable `VITE_API_BASE_URL`. The current variable points to the Render API above.

## Render configuration

The deployed Render web service uses:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan: Free
Region: Virginia (US East)
```

Private Render environment variables include `DATABASE_URL`, `DATABASE_CONNECT_TIMEOUT_SECONDS=10`, `RUN_MIGRATIONS_ON_STARTUP=false`, `JWT_SECRET`, `APP_ENV=production`, and the configured CORS origin for `https://kszarodiya-debug.github.io`. Add `AI_API_KEY` in Render to enable provider-backed assistant responses; do not place it in GitHub or frontend variables.

The designated administrator was provisioned through the one-time bootstrap command against the production database. Do not put the initial password in the Render start command or a GitHub Actions variable.

## Post-deployment smoke checks

Verify without using real student or secret data:

- `GET /health` and `GET /api/v1/health` return 200.
- `GET /openapi.json` is either protected or intentionally limited to trusted environments.
- CORS accepts only the configured frontend origin.
- Registration creates a student and does not return a password hash.
- Invalid login returns a generic 401 and repeated attempts receive 429.
- A student cannot access another user's private records or admin routes.
- A non-admin cannot read or update the admin incident queue.
- Admin incident updates create audit records.
- AI-disabled deployments return a controlled assistant-unavailable response.
- PostgreSQL connectivity and migration status are healthy.

## Monitoring and response

Monitor 401/403/404/429/5xx rates, authentication failures, migration failures, provider timeouts, database saturation, and unusual analysis/incident volume. Correlate events with `X-Request-ID` while ensuring logs do not contain passwords, bearer tokens, API keys, full message contents, or unnecessary personal data.

Prepare key rotation procedures for `JWT_SECRET`, provider credentials, database credentials, and TLS certificates. JWT secret rotation invalidates existing tokens when the signing key changes; an account-wide token-version strategy can be added if emergency selective revocation is required.

## GitHub and Pages

The repository and Pages workflow are already configured. Future changes can be published with:

```powershell
git add .
git status
git commit -m "describe the change"
git push origin main
```

GitHub Actions redeploys the frontend after workflow runs. Keep `.env`, provider credentials, database URLs, and API keys out of Git.
