# CyberSathi architecture

## System boundaries

```text
Browser (React/Vite)
        |
        | JSON + Authorization: Bearer token
        v
FastAPI API
  |-- auth, RBAC, validation, rate limits, security headers
  |-- domain services: chat, analyzers, learning, quizzes, incidents
  |-- SQLAlchemy session boundary
  |-- AI provider abstraction (optional outbound call)
        |
        v
PostgreSQL + Alembic migrations
```

The frontend and backend run independently. The backend is the trust boundary. The browser is treated as untrusted for roles, scores, report status, and object identifiers.

## Backend layers

- `app/api/routes/` defines HTTP contracts, dependencies, status codes, and role guards.
- `app/schemas/` defines Pydantic request and response validation.
- `app/services/` owns application behavior and user-scoped queries.
- `app/models/` defines SQLAlchemy persistence, constraints, indexes, timestamps, and relationships.
- `app/auth/` owns password hashing, JWT creation/verification, revocation checks, and rate limits.
- `app/ai/` isolates provider integration and defensive prompt/output boundaries.
- `app/core/` loads environment-backed configuration and validates production settings.
- `alembic/` owns explicit PostgreSQL schema changes; startup does not migrate automatically.

## Trust and data flow

1. A public registration request is validated and creates only a student account.
2. Login verifies an Argon2id hash and returns a short-lived JWT containing issuer, audience, type, subject, timestamps, and a unique identifier.
3. Authenticated requests decode the JWT, check revocation, load the user from PostgreSQL, and then apply the current database role.
4. Student services include `user_id` predicates for private records.
5. Quiz scores and awareness scores are computed server-side.
6. Admin analytics select aggregate fields only; private message bodies and incident descriptions are not used in response data.
7. Optional AI requests send only backend-approved provider messages. Provider keys never reach the browser.

## Persistence domains

- Users and roles.
- Lessons, quizzes, questions, and per-user lesson progress.
- Per-user quiz attempts and awareness scores.
- Per-user URL/email/message analysis records.
- Per-user chat history.
- Per-user incident reports.
- Revoked JWT identifiers.
- Audit records for privileged changes.

Foreign keys, check constraints, unique constraints, indexes, and timestamps are defined in the models and migrations. The current Alembic head is `20260820_0008`.

## Frontend

React routes are grouped into public, authenticated student, and admin experiences. `AuthProvider` keeps tokens in memory, attaches bearer headers through the API client, and clears the session after a 401. Frontend route guards improve UX only; backend authorization remains authoritative.

## Operational characteristics

- Security headers, explicit CORS, request IDs, generic unexpected-error responses, and no-store caching are applied by the API middleware.
- Rate limiting is currently process-local. Production deployments with multiple workers require a shared limiter and reverse-proxy controls.
- The AI provider is optional and replaceable through the provider protocol.
- URL analysis is text-only and never connects to submitted destinations.
