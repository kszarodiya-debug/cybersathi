# Alembic migrations

Run commands from `backend/` with the database URL supplied through the environment or a local, ignored `.env` file:

```powershell
alembic upgrade head
alembic downgrade -1
```

To inspect SQL without connecting to PostgreSQL:

```powershell
alembic upgrade head --sql
```

The migration environment imports SQLAlchemy metadata from `app.db.base` and never stores database credentials in the repository.
