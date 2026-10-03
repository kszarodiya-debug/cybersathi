# CyberSathi college demonstration guide

Use this walkthrough to demonstrate control of the application without revealing credentials or private student information.

## Demonstration sequence

1. Open the live frontend: <https://kszarodiya-debug.github.io/cybersathi/>.
2. Register or log in with a dedicated test account. Do not use another student's password or real sensitive incident/message data.
3. Open the backend health endpoint: <https://cybersathi-2bao.onrender.com/health> or <https://cybersathi-2bao.onrender.com/api/v1/health>.
4. In the signed-in Render account, open the CyberSathi FastAPI service (`cybersathi`) and show the service overview, deploy history, and logs without opening or copying secret values.
5. Open the associated PostgreSQL service (`cybersathi-db`) and show its service overview. Keep connection strings and passwords hidden.
6. Open pgAdmin 4 on Windows and connect using the current Render details entered privately. Follow [PGADMIN_SETUP.md](PGADMIN_SETUP.md); enter the password manually in pgAdmin.
7. Expand **Databases → public → Tables** and show the schema names. Compare them with [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
8. Run the read-only `information_schema.tables` query from [PGADMIN_SETUP.md](PGADMIN_SETUP.md). Do not edit, delete, or export private records.
9. Explain the architecture: `React → GitHub Pages → FastAPI on Render → PostgreSQL`; pgAdmin is an authorized administration client, not part of the public frontend.

## What proves control

- GitHub access: the signed-in GitHub account can view repository settings and manage the Pages workflow; a successful push proves write access, while the repository Settings page is needed to prove owner/admin role.
- Frontend control: a source change can be reviewed in a branch and built by the Pages workflow; do not make an unreviewed production change during the demo.
- Backend control: the signed-in Render account can view service settings, logs, deploy history, and environment-variable names, while keeping values hidden.
- Database control: pgAdmin authenticates to the intended Render database and the read-only catalog query returns the actual schema.

## Privacy and safety rules

Never display PostgreSQL passwords, JWT secrets, AI keys, GitHub/Render tokens, full chat conversations, submitted message contents, or unnecessary student details. Use aggregate counts or a dedicated test account. Keep the PostgreSQL service private to the backend where possible; external pgAdmin access should be temporary, encrypted, and restricted by the provider's supported controls.

The current public HTTP checks verify that the frontend and backend health endpoints are reachable. Account-level ownership and the live PostgreSQL catalog still require the signed-in GitHub/Render dashboards and the manual pgAdmin connection described above.
