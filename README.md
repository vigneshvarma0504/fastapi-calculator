# FastAPI Calculator – Secure User Model (Module 10)

A fully containerized FastAPI Calculator Web Application integrated with PostgreSQL, extended in Module 10 with a **secure user model, Pydantic validation, password hashing, database tests, and a CI/CD pipeline that builds and pushes a Docker image to Docker Hub**.

## Features

### Calculator API
- `GET /add?a=&b=`
- `GET /subtract?a=&b=`
- `GET /multiply?a=&b=`
- `GET /divide?a=&b=`

### Secure User Model
- SQLAlchemy `User` model with:
  - `id`, `username`, `email`, `password_hash`, `created_at`
  - Unique constraints on `username` and `email`
- Pydantic schemas:
  - `UserCreate` – accepts `username`, `email`, `password`
  - `UserRead` – returns `id`, `username`, `email`
- Passwords are hashed using **bcrypt** via Passlib.

### Endpoints
- `POST /users/` – create a new user (hashes password, enforces uniqueness)
- `GET /users/` – list users

## Running Locally

### 1. With virtualenv

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Use default SQLite database
uvicorn app.main:app --reload
```

## FastAPI Calculator – Module 10

This repository is a small FastAPI application used for Module 10 exercises. It demonstrates:

- SQLAlchemy models and migrations (simple declarative models)
- Pydantic v2 schemas and validation
- A small operation factory for calculator operations
- Unit and integration tests (pytest)
- A GitHub Actions workflow to run tests and build a Docker image

This module focused on modeling and validation — creating a `Calculation` model
and robust Pydantic schemas. API endpoints (BREAD) will be added in Module 12.

## What I added in Module 10

- Calculation model: `app.models.Calculation` (fields: `id`, `a`, `b`, `type`, `result`, `created_at`).
- Pydantic schemas: `app.schemas.CalculationCreate` and `CalculationRead` (includes a model validator preventing division by zero).
- Operation factory: `app.operations.OperationType` enum and `compute_result(a, b, op)` function.
- Tests:
  - `tests/test_calculations.py` unit tests for the factory and schema validation.
  - `tests/integration/test_calculations_integration.py` integration test that inserts a `Calculation` record.

## Run the project locally

1. Create and activate a Python virtual environment (recommended).

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the app (uses the default SQLite DB for local dev):

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to explore the API.

## Authentication (JWT)

This project includes JWT-based authentication for protected endpoints (calculations).

- Register a user: `POST /users/register` with JSON `{ "username": "u", "email": "e@e.com", "password": "pw" }`.
- Login to receive a token: `POST /users/login` with JSON `{ "username": "u", "password": "pw" }` — response contains `access_token`.
- Use the token when calling protected endpoints by setting the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

## Run tests locally

Run all tests with coverage:

```powershell
pytest --cov=app --cov-report=term-missing
```

Run just the calculation tests:

```powershell
pytest tests/test_calculations.py tests/integration/test_calculations_integration.py -q
```

Integration tests use `TEST_DATABASE_URL` if provided; otherwise a local SQLite file is used by default.

## Integration tests (end-to-end)

Integration tests hit the running FastAPI app using `TestClient`. To run only integration tests:

```powershell
pytest tests/integration -q
```

If you want to run integration tests against a Postgres instance, set `TEST_DATABASE_URL` to a valid Postgres DSN before running tests.

## Database migrations (Alembic)

This project includes an Alembic scaffold under `alembic/` to manage schema migrations.

Quickstart:

1. Install Alembic in your environment:

```powershell
pip install alembic
```

2. Initialize (already scaffolded here) or generate a migration:

```powershell
# generate a new revision with autogenerate
alembic revision --autogenerate -m "describe change"

# then apply migrations
alembic upgrade head
```

The `alembic/env.py` uses `DATABASE_URL` env var (defaults to local sqlite). In CI, set `DATABASE_URL` (or `TEST_DATABASE_URL`) appropriately.

## CI / GitHub Actions

Workflow: `.github/workflows/ci.yml`

- Runs pytest (unit + integration) using a Postgres service in Actions.
- Builds the Docker image in CI but only pushes if `DOCKERHUB_USERNAME` and
  `DOCKERHUB_TOKEN` secrets are configured — this avoids failing CI when
  credentials are missing. The workflow includes a debug step that prints the
  repository and tags used for the build.

### To enable pushing from CI

1. Create a Docker Hub repository under your Docker Hub account (for example: `vigneshvarma05/fastapi-calculator`).
2. In GitHub repository settings -> Secrets -> Actions add:
   - `DOCKERHUB_USERNAME` (your Docker Hub username)
   - `DOCKERHUB_TOKEN` (a Docker Hub access token with push rights)

After those are set, the workflow will log in and push the built image to Docker Hub.

### Docker Hub placeholder

This repository's CI is configured to push an image to Docker Hub when `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are set in GitHub Actions secrets. Replace the placeholder below with your actual Docker Hub repo when you enable CI pushes:

`DOCKER_HUB_REPO = your-dockerhub-username/fastapi-calculator`

## Troubleshooting CI Docker push errors

- If you see `push access denied` or `insufficient_scope` errors, confirm:
  - The Docker Hub repository exists under the username provided.
  - The `DOCKERHUB_TOKEN` is a valid access token with write/push scope.

## Next steps (optional)

- Add BREAD endpoints for `Calculation` (Module 12).
- Link calculations to users via `user_id` foreign key (if desired).
- Improve CI caching for Docker build to speed up builds.

If you want me to implement any of those next steps, tell me which one and I will proceed.
