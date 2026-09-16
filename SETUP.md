# CyberSathi setup guide

## Prerequisites

- Python 3.11 or newer.
- Node.js with pnpm or npm.
- PostgreSQL 16 or a compatible managed PostgreSQL service.
- Optional: Docker Compose for local PostgreSQL.

## Environment files

Copy the templates without committing the resulting files:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Backend variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ENV` | yes | `development`, `test`, `staging`, or `production` |
| `DATABASE_URL` | yes | SQLAlchemy PostgreSQL connection string |
| `JWT_SECRET` | yes for auth/production | Random signing secret; at least 32 characters |
| `JWT_ALGORITHM` | yes | Allow-listed HMAC algorithm, normally `HS256` |
| `JWT_ISSUER` | yes | JWT issuer claim |
| `JWT_AUDIENCE` | yes | JWT audience claim |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Short token lifetime, 5–60 minutes |
| `CORS_ORIGINS` | yes | Comma-separated explicit HTTP(S) browser origins; no wildcard. `FRONTEND_ORIGINS` remains supported for compatibility. |
| `AUTH_RATE_LIMIT_WINDOW_SECONDS` | no | Rate-limit window |
| `AUTH_LOGIN_RATE_LIMIT` | no | IP and email-keyed login limit |
| `AUTH_REGISTER_RATE_LIMIT` | no | Registration limit |
| `CHAT_RATE_LIMIT` | no | Assistant request limit |
| `ANALYSIS_RATE_LIMIT` | no | Email/URL analysis limit |
| `SUBMISSION_RATE_LIMIT` | no | Incident, lesson, quiz, and history mutation limit |
| `AI_PROVIDER` | no | `openai_compatible` to enable the configured provider |
| `AI_API_KEY` | only when AI is enabled | Provider key; backend only |
| `AI_BASE_URL` | no | Provider endpoint; HTTPS required in production |
| `AI_MODEL` | no | Provider model identifier |
| `AI_TIMEOUT_SECONDS` | no | Provider timeout |
| `AI_MAX_HISTORY_MESSAGES` | no | Number of prior turns sent to the provider |
| `ADMIN_EMAIL` | only for one-time bootstrap | Designated administrator email; backend-only |
| `ADMIN_INITIAL_PASSWORD` | only for one-time bootstrap | One-time password input, at least 16 characters; never commit it |

Frontend variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | yes | Backend API base path, for example `http://localhost:8000/api/v1` |

Never place `JWT_SECRET`, `DATABASE_URL`, `AI_API_KEY`, or PostgreSQL passwords in frontend variables.

## PostgreSQL

Using the optional local service:

```powershell
Copy-Item .env.example .env
# Replace POSTGRES_PASSWORD in .env with a local-only value.
docker compose --env-file .env up -d postgres
```

The Docker file provisions PostgreSQL only. It does not expose an application deployment or create public URLs.

Apply the schema from `backend/`:

```powershell
alembic upgrade head
```

The hosted Render deployment is configured with the same migration head and runs `alembic upgrade head` before starting the production API.

For a migration review without a live database:

```powershell
alembic upgrade head --sql
```

## Designated administrator bootstrap

Public registration always creates a `student` account and rejects an incoming `role` field. Create the designated administrator through the backend environment and a one-time initialization command; there is no public admin-registration route:

```powershell
cd backend
$env:ADMIN_EMAIL = "your-admin-email"
$env:ADMIN_INITIAL_PASSWORD = "use-a-unique-password-of-at-least-16-characters"
python -m app.bootstrap_admin
```

The command hashes the password with Argon2id, is idempotent for an existing admin with that email, and refuses to promote an existing non-admin account. Supply real values through a secret manager or private shell only. Never place them in Git, frontend variables, logs, or support tickets. On Render, run it as a one-off shell/job after migrations and before using `/admin`.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd frontend
pnpm install
pnpm run dev
```

For a production bundle:

```powershell
pnpm run build
pnpm run preview
```

## Local verification

```powershell
# backend
cd backend
python -m pytest -q
python -m compileall -q app
python -m pip check

# frontend
cd ..\frontend
pnpm run test
pnpm run lint
pnpm run build
pnpm audit --prod
```

## Troubleshooting

- A 503 from login or registration means `JWT_SECRET` is not configured in the backend environment.
- A CORS failure usually means the browser origin is missing from `CORS_ORIGINS` (or legacy `FRONTEND_ORIGINS`) or includes a path instead of an origin.
- A database error means PostgreSQL is unavailable, `DATABASE_URL` is incorrect, or migrations have not been applied.
- The assistant returns a controlled unavailable response when `AI_API_KEY` is absent; this is expected and does not affect deterministic analyzers or learning features.
