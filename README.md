# MarketMind AI

MarketMind AI is a Python backend for stock and market-price data. The current backend provides a FastAPI API, PostgreSQL persistence, and Alembic database migrations.

## Prerequisites

- Git
- Python 3.11
- Docker Desktop with Docker Compose (for the local PostgreSQL database)

## Setup From a Fresh Clone

Run these steps from PowerShell. The commands in steps 3 onward run inside `backend/`.

1. Clone the repository and enter it:

   ```powershell
   git clone https://github.com/PatelVaibhav30/MarketMind-AI.git
   cd MarketMind-AI
   ```

2. Start the local PostgreSQL service. It listens on host port `5433` and creates the `marketmind` database:

   ```powershell
   cd backend
   docker compose up -d postgres
   ```

3. Create and activate a Python virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, allow scripts for this terminal only and activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   .\.venv\Scripts\Activate.ps1
   ```

4. Install the backend dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Create your local environment file from the checked-in template:

   ```powershell
   Copy-Item .env.example .env
   ```

   The template is configured for the Compose database. `.env` is ignored by Git; keep personal credentials there and never commit them.

6. Apply database migrations:

   ```powershell
   alembic upgrade head
   ```

7. Start the API:

   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   Open <http://127.0.0.1:8000> for the service status, <http://127.0.0.1:8000/health> for the health check, or <http://127.0.0.1:8000/docs> for the interactive API documentation. Stop the server with `Ctrl+C`.

## Run Tests

Tests use a separate PostgreSQL database because the test fixtures clear database tables. In a second PowerShell terminal, from `backend/`, create it once:

```powershell
docker compose exec postgres createdb -U marketmind marketmind_test
```

Activate the virtual environment in that terminal and migrate the test database:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql+psycopg://marketmind:marketmind_dev_password@localhost:5433/marketmind_test"
alembic upgrade head
Remove-Item Env:DATABASE_URL
```

The `TEST_DATABASE_URL` in `.env` already points to this database. Run the suite with:

```powershell
pytest
```

Do not point `TEST_DATABASE_URL` at a database containing data you need; tests truncate tables.

## Configuration

Backend settings are read from `backend/.env` using the names shown in [`backend/.env.example`](backend/.env.example). The local Compose service provides PostgreSQL only; Redis and AI provider keys are optional and are not required by the current API setup. Compose uses development-only database credentials; replace them before using any non-local environment.

## Database Commands

Run these from `backend/` with the virtual environment active:

```powershell
alembic upgrade head       # apply all migrations
alembic current            # show the current database revision
alembic revision --autogenerate -m "describe change"  # create a migration
```

Commit generated migration files with the code changes they represent.

## Project Layout

```text
backend/
  app/
    api/routes/       FastAPI route handlers
    core/             Application settings and logging
    db/               SQLAlchemy database setup
    models/           SQLAlchemy models
    repositories/     Data access
    schemas/          API schemas
    services/         Application services
  alembic/            Database migration environment and revisions
  tests/              Pytest tests
  docker-compose.yml  Local PostgreSQL service
  requirements.txt    Pinned Python dependencies
```

## Stopping the Database

From `backend/`, stop the PostgreSQL container while retaining its data volume:

```powershell
docker compose down
```

To also delete the local database volume and all its data, run `docker compose down -v`.