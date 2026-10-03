# pgAdmin 4 setup for CyberSathi

This guide uses the existing Render PostgreSQL deployment. It does not create another database and does not include a password.

## Security prerequisite

Because you reported that a PostgreSQL credential was accidentally exposed during setup, rotate the database password in the Render PostgreSQL service before reconnecting. Do not send the new password to Codex or commit it. If the password is embedded in `DATABASE_URL`, update the backend service's Render environment variable with the new connection string and redeploy. Keep the value private.

## Obtain connection details privately

In Render, open the PostgreSQL service associated with the CyberSathi backend (documented service name: `cybersathi-db`) and open **Info**, **Connect**, or **Access**. Copy the current external connection details privately. Do not copy them into the repository.

Use these placeholders in your own notes:

```text
Host: <RENDER_HOST>
Port: <RENDER_PORT>
Database: <RENDER_DATABASE>
Username: <RENDER_USERNAME>
Password: <RENDER_PASSWORD>
```

The backend should use Render's private connection details when available. pgAdmin from a laptop normally requires the provider's external connection details and an encrypted connection.

## Register the server in pgAdmin 4 on Windows

1. Open **pgAdmin 4** from the Start menu. This workstation has the executable installed under `C:\Program Files\pgAdmin 4\runtime\pgAdmin4.exe`.
2. In the Browser panel, right-click **Servers** and choose **Register → Server**.
3. On **General**, enter a local label such as `CyberSathi Render PostgreSQL`.
4. On **Connection**, enter the current Render host, port, database, and username. Use the actual values privately; never replace them with values committed to Git.
5. Leave **Role** and **Service** blank unless Render explicitly supplies them.
6. Leave Kerberos disabled unless Render explicitly requires it.
7. On **SSL**, choose the mode required by the current Render connection information. For external Render connections this is commonly `require`, but confirm the current provider instructions rather than guessing.
8. Click **Save**. When pgAdmin prompts for a password, choose the option to save it only if you understand the local-machine storage implications; otherwise enter it when prompted. Enter the password manually in pgAdmin.
9. Expand the server, **Databases**, the selected database, **Schemas**, **public**, and **Tables**.

If the connection fails, re-check the rotated credential, host, port, SSL mode, firewall/network, and whether Render's external access is enabled. Do not weaken TLS or publish the database to make the connection work.

## Read-only verification queries

Open **Tools → Query Tool** and run these individually:

```sql
SELECT current_database(), current_user;
```

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;
```

This optional query reports only the server version:

```sql
SELECT version();
```

These queries do not modify data. Do not run `DROP`, `DELETE`, `TRUNCATE`, `ALTER DATABASE`, or `DROP DATABASE` as part of setup. Do not expose student records during a demonstration.

## Safe psql format

`psql` is not installed on this workstation's PATH, but the safe command format is:

```powershell
psql "postgresql://<RENDER_USERNAME>@<RENDER_HOST>:<RENDER_PORT>/<RENDER_DATABASE>?sslmode=require"
```

Use the actual non-secret values privately and enter the password at the prompt. Do not put the password in the command, PowerShell history, a script, or a GitHub Actions variable intended for frontend use.

## Ownership versus database access

Successful pgAdmin or psql access proves PostgreSQL authentication and whatever database privileges that role has. It does not prove that the Render workspace account owns the service. Separately verify Render workspace membership, service role, billing/plan permissions, deployment permissions, and backup/recovery controls in the signed-in Render dashboard.

## Backups

Open the database service's **Backups**, **Snapshots**, or **Recovery** section and confirm what the current plan supports. Do not claim a backup exists until it is visible there. If provider backups are unavailable, make an encrypted `pg_dump` from a controlled workstation only after reviewing privacy and retention requirements, and restore into a non-production database first.
