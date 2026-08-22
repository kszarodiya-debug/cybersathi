# CyberSathi deployment

CyberSathi is deployed using GitHub Pages for the frontend and Render for the FastAPI backend and PostgreSQL database. Credentials remain in provider-managed secret storage and are not committed to this repository.

Live services:

- Frontend: https://kszarodiya-debug.github.io/cybersathi/
- Backend: https://cybersathi-2bao.onrender.com
- Health: https://cybersathi-2bao.onrender.com/api/v1/health
- Repository: https://github.com/kszarodiya-debug/cybersathi

## Required production configuration

Configure secrets through the hosting platform's secret manager or environment settings:

- `APP_ENV=production`
- `DATABASE_URL` for a private PostgreSQL service, preferably with TLS parameters.
- `JWT_SECRET` generated randomly and at least 32 characters long.
- Stable `JWT_ISSUER` and `JWT_AUDIENCE` values.
- `FRONTEND_ORIGINS` containing only the real HTTPS frontend origin(s), with no wildcard.
- `VITE_API_BASE_URL` at frontend build time, pointing to the real API base path.
- `AI_API_KEY` only if the assistant is enabled.
- `AI_BASE_URL` using HTTPS in production.
- `ADMIN_EMAIL` and `ADMIN_INITIAL_PASSWORD` only during the private one-time admin bootstrap; the password must be at least 16 characters and must never be committed.

Do not put backend secrets in frontend build variables. Do not commit `.env`, `.env.*`, provider keys, database credentials, access tokens, or generated certificates.

## Database release sequence

1. Provision a private PostgreSQL database and least-privilege application role.
2. Configure `DATABASE_URL` through the secret manager.
3. Run `alembic upgrade head` from the backend image/environment. The current Render Free deployment runs this command at application startup because pre-deploy commands are unavailable on that plan.
4. Run `python -m app.bootstrap_admin` once from a private backend shell/job with `ADMIN_EMAIL` and `ADMIN_INITIAL_PASSWORD` configured. This is the only supported designated-admin provisioning path.
5. Verify the migration head and application health.
6. Encrypt backups and define retention/deletion policies for chat, analysis, incident, and audit data.

The production startup migration is fail-closed: if migration fails, the service does not accept application traffic. For a paid production deployment, move migrations to a dedicated pre-deploy or release job.

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
Start command: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan: Free
Region: Virginia (US East)
```

Private Render environment variables include `DATABASE_URL`, `JWT_SECRET`, `APP_ENV=production`, and `FRONTEND_ORIGINS=https://kszarodiya-debug.github.io`. Add `AI_API_KEY` in Render to enable provider-backed assistant responses; do not place it in GitHub or frontend variables.

The live admin console remains unavailable until the one-time bootstrap command has been run against the production database. Do not put the initial password in the Render start command or a GitHub Actions variable.

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
