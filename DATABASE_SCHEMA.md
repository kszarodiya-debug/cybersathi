# CyberSathi database schema

This document records the schema defined by the checked-in SQLAlchemy models and Alembic migrations. It deliberately does not contain production records or credentials.

## Verification boundary

| Source | Result |
| --- | --- |
| SQLAlchemy metadata | VERIFIED in `backend/app/models/` |
| Alembic configuration and migration head | VERIFIED locally; head is `20260822_0009` |
| Production catalog | NOT VERIFIED from this unauthenticated workstation audit |

The table names below are **MIGRATION/MODEL DEFINED**. They must not be described as live production tables until the read-only catalog query in [PGADMIN_SETUP.md](PGADMIN_SETUP.md) has been run against the intended Render database.

## Application tables

### `users` — MIGRATION/MODEL DEFINED

Columns: `id` integer primary key; `name` varchar(150) required; `email` varchar(320) required and unique; `password_hash` varchar(255) required; `role` varchar(20) required with allowed values `student`, `faculty`, `admin`; `department` varchar(120) nullable; `year` integer nullable and positive when present; `last_login_at` timezone-aware timestamp nullable; `created_at` and `updated_at` timezone-aware timestamps.

Indexes include email, role, department/year, and last-login time. No password or token should be returned by API responses.

### `cybersecurity_lessons` — MIGRATION/MODEL DEFINED

Columns: `id`; `title`; `description`; `introduction`; `category`; `content`; JSON `learning_objectives`; `explanation`; `real_world_example`; JSON `safety_tips`; JSON `key_takeaways`; `difficulty` with `beginner`, `intermediate`, or `advanced`; `created_at`.

Category/difficulty and category indexes support the Learning Hub.

### `quizzes` — MIGRATION/MODEL DEFINED

Columns: `id`; required `lesson_id` referencing `cybersecurity_lessons.id` with cascade delete; `title`; `description`; `category`; `difficulty`; and relationships to lesson, questions, and attempts. Indexes support lesson/title and category/difficulty lookups.

### `quiz_questions` — MIGRATION/MODEL DEFINED

Columns: `id`; required `quiz_id` referencing `quizzes.id` with cascade delete; `question`; JSONB `options`; `correct_answer`; and `explanation`. Indexed by quiz id. Correct answers are validated server-side.

### `quiz_attempts` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id` with cascade delete; `quiz_id` referencing `quizzes.id` with cascade delete; numeric `score` from 0 to 100; `total_questions` non-negative; `status` of `in_progress` or `submitted`; JSON `answers`; `started_at`; nullable `completed_at`; nullable `submitted_at`.

Indexes support user/quiz history and status filtering. Final scores are calculated by the backend.

### `lesson_progress` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id`; `lesson_id` referencing `cybersecurity_lessons.id`; `completed`; nullable `completed_at`; and `created_at`/`updated_at`. The user/lesson pair is unique and a completed record requires a completion timestamp.

### `incident_reports` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id`; `incident_type`; `description`; nullable `suspicious_url`; `occurred_at`; JSON `evidence_metadata`; `status`; `severity`; `created_at`; `updated_at`.

Status and severity are constrained to the supported values. Indexes support status/severity, incident type, and time-based queues.

### `url_analyses` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id`; `url`; numeric `risk_score` from 0 to 100; `risk_level` of `safe`, `low`, `medium`, `high`, or `critical`; `analysis_result`; JSON `detected_indicators`; `recommended_action`; `created_at`.

Indexes support user history and risk-level reporting.

### `email_analyses` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id`; `content_type` of `email`, `sms`, `whatsapp`, or `social_media`; `email_content`; numeric `risk_score` from 0 to 100; `risk_level` of `low`, `medium`, `high`, or `critical`; `analysis_result`; JSON `detected_indicators`; JSON `recommended_actions`; `safe_handling_advice`; `created_at`.

Indexes support user history and risk-level reporting. Treat submitted message content as sensitive user data.

### `chat_history` — MIGRATION/MODEL DEFINED

Columns: `id`; `user_id` referencing `users.id`; `message`; `response`; and `created_at`. Indexed by user and creation time. Administrative views should prefer aggregates and avoid exposing full conversation content unnecessarily.

### `awareness_scores` — MIGRATION/MODEL DEFINED

Columns: `id`; unique `user_id` referencing `users.id`; numeric `score`, `phishing_score`, `password_score`, `privacy_score`, `browsing_score`, and `mobile_score`, each constrained from 0 to 100; `updated_at`.

### `revoked_tokens` — MIGRATION/MODEL DEFINED

Columns: `jti` string primary key; `expires_at`; `revoked_at`. The expiry index supports cleanup and secure logout handling.

### `audit_logs` — MIGRATION/MODEL DEFINED

Columns: `id`; nullable `actor_user_id` referencing `users.id` with `SET NULL`; `action`; `entity_type`; nullable `entity_id`; JSON `details`; and `created_at`. Indexes support actor/entity investigations. Secrets must never be written to `details`.

## Safe production verification

After rotating any previously exposed database password and entering the current values privately in pgAdmin, run only the read-only statements in [PGADMIN_SETUP.md](PGADMIN_SETUP.md). Record the result locally if needed; do not commit a dump containing personal data or credentials. Compare the returned table names with this document and label the result **LIVE DATABASE VERIFIED** only after the query succeeds against the Render database.
