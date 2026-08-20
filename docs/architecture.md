# Initial architecture

CyberSathi is organized as independently runnable frontend and backend applications with an infrastructure boundary for PostgreSQL.

## Current boundary

- `frontend/` owns the browser application, visual system, and future API client layer.
- `backend/` owns the FastAPI application, configuration, versioned routes, schemas, and backend tests.
- `backend/app/db/` owns the SQLAlchemy engine, session factory, request dependency, and metadata registration.
- `backend/app/models/` owns the relational domain models and relationships.
- `backend/alembic/` owns explicit, versioned PostgreSQL schema migrations.
- `docker-compose.yml` defines PostgreSQL for local development.
- `docs/` holds decisions and operational notes that should remain separate from implementation code.

## API baseline

- `GET /health` is a lightweight liveness route.
- `GET /api/v1/health` is the versioned equivalent for clients.
- Health checks do not require a database connection, so process availability can be diagnosed independently from persistence availability.

## Initial persistence schema

The first migration creates users, lessons, quizzes, questions, attempts, incident reports, URL/email analyses, chat history, and one current awareness score per user. Foreign keys use cascading deletes for user-owned records, and score/risk/role/status values are constrained at the database layer.

Migration `20260820_0007` adds quiz categories and difficulty metadata, an in-progress/submitted attempt lifecycle, server-owned answer storage, seeded quizzes, and the mobile-security awareness dimension. Quiz routes never return correct answers before submission; the backend validates and grades every answer, then recalculates the authenticated user's awareness score.

Migration `20260820_0008` adds the student incident workflow with normalized uppercase status/severity values, occurrence timestamps, minimal evidence metadata, and an `audit_logs` table. Student report queries are always filtered by the authenticated user; administrative report reads and updates require the admin role. Audit records contain only the actor, action, report identifier, and before/after workflow values—not report descriptions or evidence content.

## Authentication baseline

- Registration always creates a `student`; faculty and admin accounts must be provisioned through a trusted administrative workflow.
- Passwords are stored only as Argon2id hashes.
- JWT access tokens include subject, role, type, issued-at, expiry, and unique identifier claims.
- Logout records the token identifier in `revoked_tokens` until expiry. The frontend also clears its in-memory token immediately.
- Role checks use the current database user role rather than trusting a stale role claim in the token.
- Login and registration have per-process sliding-window rate limits. A shared limiter such as Redis is recommended for multiple API workers.
- Protected route shells currently cover student, faculty, and admin capabilities without implementing future business workflows prematurely.

## Security baseline

- Secrets and connection strings are loaded from environment variables.
- `.env.example` files contain placeholders only and are safe templates, not credentials.
- CORS origins are explicitly configured rather than wildcarded.
- Future authentication, authorization, validation, and persistence should be added behind the existing application boundaries.
