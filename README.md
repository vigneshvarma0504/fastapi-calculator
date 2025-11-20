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

Open: http://127.0.0.1:8000/docs

### 2. With Docker Compose (Postgres)

```bash
docker compose up --build
```

This starts:
- `db` – Postgres
- `web` – FastAPI app at http://localhost:8000

## Running Tests Locally

By default integration tests use `sqlite:///./test_integration.db`.

```bash
pytest --cov=app --cov-report=term-missing
```

To run tests against a Postgres database:

```bash
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/calculator_db
pytest
```

## CI/CD Pipeline (GitHub Actions → Docker Hub)

- Workflow file: `.github/workflows/ci.yml`
- Uses a Postgres service container for integration tests.
- On successful tests:
  - Builds a Docker image.
  - Tags and pushes to Docker Hub as:

    ```text
    ${{ secrets.DOCKERHUB_USERNAME }}/fastapi-calculator:latest
    ```

### Required GitHub Secrets

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (Docker Hub access token)

## Reflection

See `reflection_module10.md` for a short reflection on:
- Password hashing and Pydantic validation.
- Hurdles with Docker Hub authentication, environment variables, and CI.
