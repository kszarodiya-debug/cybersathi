# CyberSathi owner access guide

This guide describes independent owner administration without storing passwords, API keys, JWT secrets, database credentials, or private tokens.

## Current deployment

| Component | Value | Status |
| --- | --- | --- |
| Frontend | https://kszarodiya-debug.github.io/cybersathi/ | Live |
| Backend | https://cybersathi-2bao.onrender.com | Live; health endpoints previously returned 200 |
| Repository | https://github.com/kszarodiya-debug/cybersathi | Public; signed-in account role must be verified |
| Branch | `main` | Local checkout tracks `origin/main` at `dd01303` |
| Render web service | `cybersathi` / `srv-da3adjuk1f9s73eedj7g` | Service identity known; account role unknown |
| PostgreSQL | Existing Render deployment, documented as `cybersathi-db` | Owner role and live schema require dashboard access |

No new provider or database was created during this audit.

## GitHub and frontend control

Sign in to the GitHub account that owns or administers the repository. Verify **Settings → Collaborators and teams** shows Owner or Admin, inspect **Settings → Branches** for `main` protection, confirm **Settings → Actions → General** is enabled, and confirm **Settings → Pages** uses **GitHub Actions**.

This Windows checkout's GitHub CLI reports the active account as `kszarodiya-debug` with a redacted token. That verifies local CLI authentication only; it does not by itself prove the repository-owner role. Confirm the role in the repository settings while signed in.

In **Settings → Secrets and variables → Actions → Variables**, verify `VITE_API_BASE_URL` is `https://cybersathi-2bao.onrender.com/api/v1`. It must not contain credentials. The workflow is `.github/workflows/deploy-pages.yml`; it builds the app, uses the project base path, adds the SPA fallback, and deploys the artifact. A successful workflow for `dd01303` was observed.

Clone and manage:

```powershell
git clone https://github.com/kszarodiya-debug/cybersathi.git
cd cybersathi
git switch main
git pull --ff-only origin main
```

Frontend code is in `frontend/src`; API requests are centralized in `frontend/src/services/api.ts`; the base path is in `frontend/vite.config.ts`; local API configuration is `frontend/.env.example`. The live bundle was checked and contains the Render API origin, not localhost.

Local frontend commands: `cd frontend`, `pnpm install --frozen-lockfile`, copy `.env.example` to `.env`, set `VITE_API_BASE_URL`, then `pnpm run dev`. Verify with `pnpm run lint`, `pnpm run test -- --run`, and `pnpm run build`. Use npm only when pnpm is unavailable; the checked-in lockfile is `frontend/pnpm-lock.yaml`.

## Backend and Render control

`backend/app/main.py` is the FastAPI entry point. Routes are under `backend/app/api/routes/`; auth and RBAC are under `backend/app/auth/`; environment configuration is `backend/app/core/config.py`; SQLAlchemy models are under `backend/app/models/`; migrations are under `backend/alembic/`; AI controls are under `backend/app/ai/`; domain logic is under `backend/app/services/`.

Run locally: create a Python virtual environment in `backend`, install `requirements.txt`, copy `.env.example` to `.env`, replace development placeholders, run `alembic upgrade head`, then run `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.

Local `/docs` and `/redoc` are available. Production disables `/docs`, `/redoc`, and `/openapi.json` through `backend/app/main.py`.

To deploy: run tests and migration checks, push the approved commit to `main`, open Render service `cybersathi`, use **Manual Deploy → Deploy latest commit** when configured, inspect **Events/Deploys/Logs**, and verify `/health` and `/api/v1/health`. Render **Settings** manages source, root directory, commands, health checks, networking, and custom domains. **Environment** manages secret names and values. Never paste secrets into code, commits, logs, or frontend variables.

## Environment variables

Backend variable names include `DATABASE_URL`, `JWT_SECRET`, JWT issuer/audience/expiry settings, `CORS_ORIGINS` (preferred) or legacy `FRONTEND_ORIGINS`, rate limits, `AI_PROVIDER`, `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`, and one-time `ADMIN_EMAIL`/`ADMIN_INITIAL_PASSWORD`. Inspect or rotate them in Render **Environment → Edit** without disclosing values. Public registration cannot self-assign `admin`.

## PostgreSQL owner access

The React frontend never connects directly to PostgreSQL. Sign in to Render, open the PostgreSQL service associated with `cybersathi` (documented service name `cybersathi-db`), and open **Info**, **Connect**, or **Access**. Obtain host, port, database, username, and password privately. Prefer internal connection details for backend traffic; use external details only from a controlled workstation.

The exact live database association, credentials, backup availability, and owner role cannot be verified from public HTTP/Git data. Do not treat this guide as proof of database access until the signed-in Render dashboard confirms it.

### pgAdmin

pgAdmin 4 is installed on this Windows workstation at `C:\Program Files\pgAdmin 4\runtime\pgAdmin4.exe`, but it is not on PATH. Create a server using Render's private host, port (normally `5432`), database, username, and password. Set SSL mode to the Render-specified mode; external Render connections normally use `require`. Test read-only with `SELECT current_database(), current_user, version();`. For the full procedure, see [PGADMIN_SETUP.md](PGADMIN_SETUP.md). Enter the password manually in pgAdmin.

### psql

Never put the password in shell history: `psql "postgresql://USERNAME@HOST:5432/DATABASE?sslmode=require"`. Enter the password at the prompt.

### Backups

Inspect the database service's **Backups**, **Snapshots**, or **Recovery** section. Current-plan support was not independently verifiable from this unauthenticated audit. Do not claim a backup exists until visible in Render. If unavailable, create encrypted `pg_dump` backups from a controlled workstation and restore only into a non-production database.

## Migration-defined schema

The migrations/models define `users`, `cybersecurity_lessons`, `quizzes`, `quiz_questions`, `quiz_attempts`, `incident_reports`, `url_analyses`, `email_analyses`, `chat_history`, and `awareness_scores`. Supporting tables are `lesson_progress`, `revoked_tokens`, and `audit_logs`. These are migration-defined names, not a direct production catalog dump.

Confirm the actual production catalog privately with the read-only query in [PGADMIN_SETUP.md](PGADMIN_SETUP.md). The expanded model/migration inventory is in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Admin and security proof

Unauthenticated `GET /api/v1/admin/stats` was verified to return HTTP 401. Backend tests cover student/faculty denial, admin access, unauthenticated denial, registration role restrictions, data minimization, and incident authorization. The backend role guard is the security boundary; frontend hiding is not.

Keep MFA enabled for GitHub and Render. Rotate JWT, database, and AI secrets through provider settings, redeploy, and run health/authorization checks. Rotating `JWT_SECRET` invalidates existing access tokens.

## Ownership audit

| Area | Result | Next verification |
| --- | --- | --- |
| GitHub account owner | UNKNOWN | Verify GitHub Settings while signed in |
| GitHub repository write access | WRITE VERIFIED historically | A push to `main` succeeded; this does not prove ownership |
| Render backend owner/admin | UNKNOWN | Verify workspace/service role in Render |
| Render PostgreSQL owner/admin | UNKNOWN | Verify database role in Render |
| GitHub Pages | CONTROLLED BY WORKFLOW | Verify account role and Pages settings |
| Direct database access | UNKNOWN | Obtain Connect/Info values and test privately |
| pgAdmin | NOT READY until values are entered privately | Follow pgAdmin procedure |
| psql | READY as a procedure; credentials unverified | Use password prompt and SSL |
| Backend deployment control | UNKNOWN | Verify Render role |
| Frontend deployment control | UNKNOWN at account-role level | Verify GitHub Admin permission |
| Database administration | UNKNOWN | Verify Render database role and backups |

## Remaining manual actions

1. Verify GitHub Admin permission, `main` rules, Actions, and Pages.
2. Verify Render membership/owner role for `cybersathi` and `cybersathi-db`.
3. Privately copy database details from Render and connect with pgAdmin or psql.
4. Run the schema query and compare it with the migration-defined tables.
5. Inspect Render backup/recovery capabilities for the current plan.
6. Add a real `AI_API_KEY` in Render only if provider-backed AI is required; never send it to Codex or commit it.
