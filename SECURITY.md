# CyberSathi Security

CyberSathi is a defensive cybersecurity-awareness platform for college students, faculty, and administrators. This document describes the security controls in the current application and the operational assumptions required for a safe deployment.

## Security architecture

- The frontend is a React/Vite application. Access tokens are held in React memory only; they are not written to `localStorage`, `sessionStorage`, cookies, or URL parameters.
- The backend is a FastAPI service using Pydantic validation, SQLAlchemy parameterized queries, PostgreSQL, and Alembic migrations.
- Passwords are stored only as Argon2id hashes through `pwdlib`; password hashes are excluded from response schemas.
- Access tokens are short-lived JWTs with a unique `jti`, `iat`, `exp`, issuer, audience, and explicit access-token type. Logout persists the `jti` in the revoked-token table until expiration.
- Authorization is enforced from the current database user loaded from the token subject. The role claim is not trusted for authorization decisions.
- Student-owned endpoints are restricted to `student` accounts. Faculty and administrator access is provided only through explicitly permitted routes.
- Administrator changes to users and incident reports are recorded in the audit log without copying report content, URLs, or evidence into the audit record.
- All external AI calls go through a backend provider abstraction. API keys are server-side environment variables, provider calls have timeouts, and prompts/output are bounded by defensive safety controls.

## Threat model

The primary threats are:

- credential stuffing, password spraying, and registration abuse;
- stolen, forged, expired, or replayed access tokens;
- broken object-level authorization exposing another student's dashboard, analysis, chat, lesson progress, quiz attempts, or reports;
- malicious or oversized input, including prompt-injection content and suspicious URLs/messages;
- cross-origin abuse, browser framing, MIME confusion, caching of private responses, and reflected/stored XSS;
- unauthorized administrative changes and insufficient auditability;
- denial of service through expensive analysis, quiz, incident, or AI requests;
- accidental exposure of secrets, message content, student data, or provider credentials.

The platform does not assume that a frontend role, client-provided score, URL, severity, or status is trustworthy. The backend validates and derives security-sensitive values.

## Authentication

- Registration always creates the `student` role. Elevated roles must be provisioned separately.
- Login errors are intentionally generic and do not reveal whether an email exists.
- Password input is validated by Pydantic and hashed with Argon2id. Plaintext passwords are never persisted or returned.
- JWT signing uses an environment-provided secret and an allow-listed HMAC algorithm. Production startup requires a secret of at least 32 characters.
- Tokens include issuer and audience claims and both are verified during decoding.
- Token revocation is checked on every authenticated request. Tokens are short-lived by configuration, with a maximum configured lifetime of 60 minutes.
- The browser clears its in-memory session after a 401 response and calls logout to revoke the active token when possible.

Required production variables include `JWT_SECRET`, `DATABASE_URL`, `FRONTEND_ORIGINS`, and, when the assistant is enabled, `AI_API_KEY`. Never commit a real `.env` file.

## Authorization and endpoint review

The backend route groups were reviewed individually:

| Route group | Protection and result |
|---|---|
| `/health`, `/api/v1/health` | Public liveness only; returns no database data or secrets. Security headers and no-store caching are applied. |
| `/api/v1/auth/register` | Public, creates only students, validates input, rate-limited, generic conflict handling. |
| `/api/v1/auth/login` | Public, Argon2id verification, generic failures, rate-limited. |
| `/api/v1/auth/me` | Authenticated; returns the current database user without credentials. |
| `/api/v1/auth/logout` | Authenticated; revokes only the presented token. |
| `/api/v1/chat/*` | Student-only, user-scoped history, bounded input, provider timeout/error mapping, output safety filtering, rate-limited. |
| `/api/v1/students/analysis/messages`, `/emails`, `/urls` | Student-only, bounded/validated input, deterministic non-invasive analysis, user-scoped storage, rate-limited. |
| `/api/v1/students/analysis/urls/history` | Student-only and filtered by the authenticated user id. |
| `/api/v1/students/dashboard` | Student-only; every aggregation query is user-scoped. |
| `/api/v1/students/lessons/*` | Student-only; lesson progress is keyed by authenticated user id; completion is rate-limited. |
| `/api/v1/students/quizzes/*` | Student-only; attempts and history are user-scoped, answers are validated and graded server-side, start/submit are rate-limited. |
| `/api/v1/students/incidents/*` | Student-only; students can read only their own reports; creation validates URL/time/metadata and is rate-limited. |
| `/api/v1/admin/analytics`, `/users`, `/lessons`, `/quizzes` | Admin-only from the database role; analytics expose aggregates, management responses omit password hashes, and user role changes are audited. |
| `/api/v1/admin/incidents/*` | Admin-only; status/severity are allow-listed and changes are audited. |
| `/api/v1/faculty/*` | Faculty/admin role-gated placeholders; no private student records are exposed by these shells. |

SQL access uses SQLAlchemy expressions and bound parameters. No route concatenates user input into SQL. Student object lookups include the authenticated user id where the object is private; an unauthorized quiz attempt or incident is returned as not found rather than disclosed.

## Browser and API protections

- CORS accepts only explicit HTTP(S) origins from `FRONTEND_ORIGINS`; wildcard origins are rejected and credentials mode is disabled because the app uses bearer tokens rather than cookies.
- Allowed methods and headers are explicit, including `DELETE` for chat-history clearing and `Authorization` for bearer tokens.
- Responses include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, a restrictive API CSP, `Cache-Control: no-store`, and a request correlation id. Production adds HSTS.
- React escapes displayed user content and the codebase does not use `dangerouslySetInnerHTML`, `innerHTML`, `eval`, or dynamic script injection.
- CSRF tokens are not required for the current bearer-token architecture because authentication is not cookie-based. If cookie authentication is introduced, add SameSite, Secure, HttpOnly cookies and CSRF protection before enabling it.
- There are no upload or file-processing endpoints. Do not add one without content-type allow-lists, size limits, malware scanning, storage isolation, and non-executable storage.
- Validation rejects control characters in text/URLs, limits message/description sizes, validates HTTP(S) URL syntax, bounds metadata, and allow-lists roles, incident states, severities, and content types.

## Rate limiting and audit logging

Authentication, assistant, message/URL analysis, lesson completion, quiz attempts, incident submission, and chat-history deletion are rate-limited per client address. The current limiter is in-process and suitable only for a single-process deployment. Multi-worker or multi-instance production deployments must move limiter state to a shared store such as Redis and enforce limits at the reverse proxy as well.

Administrative user and incident changes create audit records containing actor, action, entity, and before/after state where applicable. Audit records intentionally do not duplicate sensitive content.

## Data protection

- Keep PostgreSQL on a private network and use TLS for database connections in production.
- Use a least-privilege database role; the application role should not own unrelated databases or server-level objects.
- Encrypt database backups and restrict access to chat, analysis, incident, and audit tables.
- Establish retention and deletion policies for message content, URLs, incident descriptions, and audit logs before production use.
- Set `AI_BASE_URL` to a trusted HTTPS provider in production. Do not send secrets or unnecessary personal data to an AI provider.

## Dependency and deployment checks

Backend dependencies are declared in `backend/requirements.txt`; frontend dependencies are locked in `frontend/pnpm-lock.yaml`. Run the package-manager audit commands in CI, keep lockfiles under review, and rebuild images from current base images. Run migrations as a controlled deployment step, never from an untrusted request.

The application should run behind a TLS-terminating reverse proxy with request-size limits, connection/time limits, access logging with secret redaction, and a shared rate limiter. Do not expose PostgreSQL directly to the public internet.

## Known limitations

- The built-in limiter is process-local and does not provide distributed abuse prevention.
- JWT revocation is stored per token; a full account-wide logout or emergency key rotation requires an additional token-version/deny-list strategy.
- The deterministic email and URL analyzers are indicators, not verdicts, and do not replace a trusted reputation service or incident-response process.
- The assistant can still produce imperfect educational output; safety filtering is a defense-in-depth control, not a proof of correctness.
- Faculty reporting permissions are currently represented by limited role-gated route shells and should be refined with institution-specific data-minimization rules before enabling broader reporting.
- Dependency vulnerability status depends on running current audit tooling against the lockfiles and deployment environment.

## Responsible-use policy

CyberSathi is for awareness, prevention, authorized testing, incident reporting, and recovery. Do not use it to obtain credentials, deploy malware, evade detection, access systems without permission, disrupt services, or target people. The assistant must remain educational and defensive. Report suspected vulnerabilities through the project's approved maintainer channel with reproduction details that avoid real secrets and unnecessary personal data.
