# CYBERSATHI

## AI Cybersecurity Awareness Assistant

CyberSathi is a college-focused cybersecurity awareness platform for students, faculty, and administrators. It combines practical learning, defensive analysis tools, quizzes, incident reporting, awareness scoring, and a safety-bounded AI assistant.

## Features

- Student registration, login, logout, JWT authentication, and role-based access control.
- Student dashboard with awareness scores, learning progress, quiz activity, analyses, and incident history.
- Learning Hub with database-backed lessons, categories, filtering, completion tracking, and seeded content.
- Backend-graded cybersecurity quizzes with explanations, attempt history, and awareness-score calculation.
- Defensive email/message analyzer for phishing, urgency, impersonation, credential requests, financial scams, links, attachments, OTPs, and social engineering.
- Non-invasive URL analyzer for syntax, HTTPS, hostname, IP hosts, punycode/IDN, suspicious keywords, query parameters, and impersonation patterns.
- CyberSathi assistant with private chat history, provider abstraction, timeouts, rate limiting, prompt-injection boundaries, and defensive-only responses.
- Incident reporting for students and an admin review queue with status/severity updates and audit logging.
- Admin dashboard with aggregate awareness, incident, quiz, email-analysis, and URL-analysis statistics.
- Responsive React UI with reusable components, loading states, empty states, error states, and accessible controls.

## Screenshots and placeholders

The repository currently contains the UI implementation but no committed screenshot assets. Add review captures under `docs/screenshots/` when available:

- `docs/screenshots/landing-page.png` — landing page placeholder
- `docs/screenshots/student-dashboard.png` — student dashboard placeholder
- `docs/screenshots/admin-dashboard.png` — admin dashboard placeholder

Do not place credentials, tokens, real student data, or sensitive incident content in screenshots.

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Authentication | Argon2id password hashing, JWT access tokens, revocation, RBAC |
| AI boundary | Backend provider abstraction with defensive safety controls |
| Testing | Pytest, Vitest, React Testing Library |

## Architecture

```text
frontend/                 React browser application
  src/components/         Reusable UI components
  src/pages/               Route-level pages
  src/services/            API client boundary
backend/                  FastAPI service
  app/api/routes/          Versioned HTTP endpoints
  app/auth/                Passwords, JWTs, role guards, rate limits
  app/core/                Environment-backed configuration
  app/db/                  SQLAlchemy engine, sessions, metadata
  app/models/              PostgreSQL persistence models
  app/schemas/             Pydantic validation and response contracts
  app/services/            Domain and aggregation logic
  alembic/                 Versioned database migrations
docs/                      API and architecture notes
```

The browser sends bearer tokens held in memory. The backend loads the current user from the database and makes authorization decisions from the database role, not from frontend state or a stale JWT role claim. Student-owned queries include the authenticated user id. See [ARCHITECTURE.md](ARCHITECTURE.md), [docs/API.md](docs/API.md), and [SECURITY.md](SECURITY.md).

## Installation

Prerequisites:

- Python 3.11+ with PostgreSQL client support.
- Node.js and pnpm/npm.
- PostgreSQL 16+ for a real database.
- Docker Compose is optional for local PostgreSQL; it was not available in the verification environment.

Create local environment files from the checked-in templates:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Replace every placeholder secret in `backend/.env`. Never commit either `.env` file.

## Environment variables

Backend variables are documented in [SETUP.md](SETUP.md), including `DATABASE_URL`, `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `FRONTEND_ORIGINS`, rate limits, and optional AI-provider settings. The frontend uses `VITE_API_BASE_URL` only; it must never contain an API key or database credential.

## Database setup

Start PostgreSQL using an approved local installation or the supplied Compose file:

```powershell
docker compose --env-file .env up -d postgres
```

From `backend/`, apply migrations explicitly for local development:

```powershell
alembic upgrade head
```

The current migration head is `20260820_0008`. In the Render production deployment, the backend applies migrations before accepting traffic because the free Render tier does not provide a pre-deploy command.

## Running the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health endpoints:

- `GET /health`
- `GET /api/v1/health`

Interactive OpenAPI documentation is available at `/docs` when the service is running. Do not expose interactive API documentation publicly without an access and network policy.

## Running the frontend

```powershell
cd frontend
pnpm install
pnpm run dev
```

The default Vite development origin is `http://localhost:5173`; configure `VITE_API_BASE_URL` to match the backend API prefix.

## Testing and quality checks

Backend:

```powershell
cd backend
python -m pytest -q
python -m compileall -q app
alembic heads
alembic upgrade head --sql
python -m pip check
```

Frontend:

```powershell
cd frontend
pnpm run test
pnpm run lint
pnpm run build
pnpm audit --prod
```

The final verification run passed 42 backend tests, 4 frontend tests, frontend lint, the production build, Python compilation, dependency consistency, and the npm production audit.

## Deployment

Current deployment:

- Frontend: [GitHub Pages](https://kszarodiya-debug.github.io/cybersathi/)
- Backend API: [Render](https://cybersathi-2bao.onrender.com)
- API health: [https://cybersathi-2bao.onrender.com/api/v1/health](https://cybersathi-2bao.onrender.com/api/v1/health)
- Database: Render PostgreSQL service `cybersathi-db` on the Free plan
- Pages workflow: `.github/workflows/deploy-pages.yml`

The Render Free plan is suitable for testing and may sleep or expire. Configure `AI_API_KEY` privately in Render to enable the AI assistant. See [DEPLOYMENT.md](DEPLOYMENT.md) for the production checklist and provider configuration.

## Security considerations

- Use a randomly generated production `JWT_SECRET` of at least 32 characters.
- Use explicit HTTPS frontend origins; wildcard CORS is rejected.
- Keep PostgreSQL private and use encrypted connections/backups in production.
- Put the API behind TLS, request-size limits, proxy timeouts, access-log redaction, and a shared rate limiter for multi-worker deployments.
- Do not treat analyzer results as deterministic verdicts.
- Do not send passwords, OTPs, API keys, or unnecessary personal data to the assistant.
- Review [SECURITY.md](SECURITY.md) before enabling production traffic.

## GitHub preparation

The project is published at [github.com/kszarodiya-debug/cybersathi](https://github.com/kszarodiya-debug/cybersathi). Future changes pushed to `main` automatically rebuild the GitHub Pages frontend. Render deployments are currently triggered manually because the public-repository service is configured on the Free plan.
