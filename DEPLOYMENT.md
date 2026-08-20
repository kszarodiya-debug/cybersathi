# CyberSathi deployment preparation

This repository does not contain deployment credentials, infrastructure accounts, certificates, provider keys, or a deployment URL. The instructions below are provider-neutral and must be adapted to the chosen hosting platform.

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

Do not put backend secrets in frontend build variables. Do not commit `.env`, `.env.*`, provider keys, database credentials, access tokens, or generated certificates.

## Database release sequence

1. Provision a private PostgreSQL database and least-privilege application role.
2. Configure `DATABASE_URL` through the secret manager.
3. Run `alembic upgrade head` as a controlled release job from the backend image/environment.
4. Verify the migration head and application health.
5. Encrypt backups and define retention/deletion policies for chat, analysis, incident, and audit data.

The application does not migrate automatically at startup. This prevents an application request from becoming a schema-changing operation.

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

## GitHub preparation

The current workspace is not initialized as a Git repository. After reviewing the files and confirming no secrets are present:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Prepare CyberSathi for deployment"
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

Replace the placeholder remote only after creating or selecting the intended repository. No deployment URL is assumed by this project.
