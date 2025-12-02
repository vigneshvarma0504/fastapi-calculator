# FastAPI Calculator – Complete Backend (Module 12)

A fully containerized FastAPI Calculator Web Application integrated with PostgreSQL with **secure user management, JWT authentication, Calculation BREAD endpoints, comprehensive integration tests, and CI/CD pipeline that automatically tests and deploys to Docker Hub**.

## Features

### Core Calculator Operations
- `GET /add?a=&b=` – Simple addition
- `GET /subtract?a=&b=` – Simple subtraction
- `GET /multiply?a=&b=` – Simple multiplication
- `GET /divide?a=&b=` – Simple division (with zero check)

### User Management
- **Registration**: `POST /users/register` – Create a new user
- **Login**: `POST /users/login` – Get JWT access & refresh tokens
- **Token Refresh**: `POST /users/refresh` – Refresh expired access tokens
- **Logout**: `POST /users/logout` – Revoke refresh tokens
- **Token Management**: List and revoke tokens at user level
- **Admin Features**: Manage users, tokens, and roles

### Calculation Endpoints (BREAD)
All calculation endpoints require JWT authentication via `Authorization: Bearer <token>`

- **Browse** (GET `/calculations`) – List all calculations with pagination
- **Read** (GET `/calculations/{id}`) – Retrieve a specific calculation
- **Edit** (PUT `/calculations/{id}`) – Update a calculation's operands/operation
- **Add** (POST `/calculations`) – Create a new calculation
- **Delete** (DELETE `/calculations/{id}`) – Remove a calculation

### Security Features
- JWT-based authentication (access & refresh tokens)
- Password hashing using PBKDF2-SHA256
- User roles (admin, user)
- Refresh token revocation and management
- SQLAlchemy ORM with Pydantic validation

## Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 13+ (for production/CI)
- Docker & Docker Compose (optional, for containerization)

### Local Setup (Development)

1. **Clone the repository** and navigate to the project directory:
```powershell
cd fastapi-calculator-main
```

2. **Create a virtual environment**:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**:
```powershell
pip install -r requirements.txt
```

4. **Run the application** (uses SQLite locally by default):
```powershell
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`

## Using the API

### OpenAPI Documentation
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### User Registration & Login Flow

#### 1. Register a new user
```bash
curl -X POST "http://127.0.0.1:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secure_password_123"
  }'
```

Response:
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "role": "user"
}
```

#### 2. Login and get tokens
```bash
curl -X POST "http://127.0.0.1:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "secure_password_123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Use access token to create a calculation
```bash
curl -X POST "http://127.0.0.1:8000/calculations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "a": 10,
    "b": 5,
    "type": "Add"
  }'
```

Response:
```json
{
  "id": 1,
  "a": 10,
  "b": 5,
  "type": "Add",
  "result": 15,
  "created_at": "2025-12-02T03:00:00"
}
```

### Calculation Examples

#### Create a calculation
```bash
curl -X POST "http://127.0.0.1:8000/calculations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "a": 20,
    "b": 4,
    "type": "Divide"
  }'
```

#### Get all calculations
```bash
curl -X GET "http://127.0.0.1:8000/calculations?skip=0&limit=10" \
  -H "Authorization: Bearer <token>"
```

#### Get a specific calculation
```bash
curl -X GET "http://127.0.0.1:8000/calculations/1" \
  -H "Authorization: Bearer <token>"
```

#### Update a calculation
```bash
curl -X PUT "http://127.0.0.1:8000/calculations/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "a": 30,
    "b": 6,
    "type": "Multiply"
  }'
```

#### Delete a calculation
```bash
curl -X DELETE "http://127.0.0.1:8000/calculations/1" \
  -H "Authorization: Bearer <token>"
```

## Running Tests

### Run All Tests with Coverage
```powershell
pytest --cov=app --cov-report=term-missing
```

### Run Only Unit Tests
```powershell
pytest tests/ -q
```

### Run Only Integration Tests
```powershell
pytest tests/integration/ -q
```

### Run Integration Tests with PostgreSQL
Set the database URL before running tests:
```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/calculator_db"
pytest tests/integration/ -v
```

### Test Coverage Report
After running tests with coverage:
```powershell
pytest --cov=app --cov-report=html
```
This generates an HTML report in `htmlcov/index.html`

## Docker & Docker Compose

### Build the Docker Image
```bash
docker build -t fastapi-calculator:latest .
```

### Run with Docker Compose (includes PostgreSQL)
```bash
docker-compose up -d
```

The application will be accessible at http://localhost:8000

To stop the containers:
```bash
docker-compose down
```

## GitHub Actions CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. **Runs on every push to `main` and pull requests**
2. **Spins up a PostgreSQL service** for integration testing
3. **Runs all tests** with coverage reporting
4. **Builds a Docker image** on successful test run
5. **Pushes to Docker Hub** (if credentials are configured)

### Setting Up Docker Hub Integration

1. Create a Docker Hub account and a new repository (e.g., `username/fastapi-calculator`)

2. In GitHub repository settings, go to **Secrets and Variables → Actions** and add:
   - `DOCKERHUB_USERNAME` – Your Docker Hub username
   - `DOCKERHUB_TOKEN` – A Docker Hub Personal Access Token with push permissions
   - `DOCKER_HUB_REPO` – Your full Docker Hub repo name (e.g., `username/fastapi-calculator`)

3. After setting these secrets, the workflow will automatically:
   - Build the image
   - Tag it with `latest` and the commit SHA
   - Push to Docker Hub on successful test run

### Example Workflow Run
```
Workflow triggered on: push to main
✓ Checkout code
✓ Set up Python
✓ Install dependencies
✓ Start PostgreSQL service
✓ Run tests (--cov=app)
✓ Build Docker image
✓ Push to Docker Hub as username/fastapi-calculator:latest and username/fastapi-calculator:<sha>
```

## Project Structure

```
fastapi-calculator-main/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app & endpoints
│   ├── models.py                # SQLAlchemy models (User, Calculation, RefreshToken)
│   ├── schemas.py               # Pydantic schemas
│   ├── security.py              # JWT & password hashing utilities
│   ├── database.py              # Database configuration
│   ├── operations.py            # Calculator operations
│   └── logger_config.py
├── tests/
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_calculations.py
│   ├── test_database.py
│   ├── test_schemas.py
│   ├── test_security.py
│   └── integration/
│       ├── __init__.py
│       ├── test_calculation_endpoints.py    # BREAD endpoint tests
│       ├── test_calculations_integration.py
│       └── test_users_integration.py        # User registration/login tests
├── alembic/                      # Database migration scripts
├── .github/workflows/ci.yml       # GitHub Actions CI/CD workflow
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## API Endpoints Summary

### User Endpoints
- `POST /users/register` – Register a new user
- `POST /users/login` – Login and get tokens
- `POST /users/refresh` – Refresh access token
- `POST /users/logout` – Logout (revoke refresh token)
- `GET /users/me/tokens` – List current user's tokens
- `DELETE /users/me/tokens/{token_id}` – Revoke a specific token
- `POST /users/me/revoke` – Revoke token by string

### Calculation Endpoints (Protected)
- `GET /calculations` – List all calculations
- `POST /calculations` – Create a new calculation
- `GET /calculations/{id}` – Get calculation by ID
- `PUT /calculations/{id}` – Update calculation
- `DELETE /calculations/{id}` – Delete calculation

### Simple Operations (Unprotected)
- `GET /add?a=5&b=3` – Returns `{"operation": "add", "a": 5, "b": 3, "result": 8}`
- `GET /subtract?a=10&b=4` – Returns `{"operation": "subtract", ...}`
- `GET /multiply?a=6&b=7` – Returns `{"operation": "multiply", ...}`
- `GET /divide?a=20&b=4` – Returns `{"operation": "divide", ...}`

### Admin Endpoints (Admin role required)
- `GET /users/` – List all users
- `GET /admin/users` – List users with token count
- `POST /users/{username}/role` – Change user role
- `GET /admin/users/{username}/tokens` – List tokens for a user
- `POST /users/{username}/revoke_all` – Revoke all tokens for a user
- `POST /admin/tokens/revoke` – Admin revoke by token string
- `GET /admin/tokens` – List all tokens

## Environment Variables

- `DATABASE_URL` – PostgreSQL connection string (default: `sqlite:///./test.db`)
- `TEST_DATABASE_URL` – Test database URL (default: `sqlite:///./test_integration.db`)
- `SECRET_KEY` – JWT secret key (default: `dev-secret-change-me` – **change in production!**)
- `ACCESS_TOKEN_EXPIRE_MINUTES` – Token expiry in minutes (default: 1440 = 24 hours)

## Troubleshooting

### PostgreSQL Connection Issues
- Ensure PostgreSQL is running: `psql --version`
- Check connection string format: `postgresql://user:password@host:port/dbname`
- For WSL/Docker on Windows, use `host.docker.internal` instead of `localhost`

### JWT Token Errors
- Tokens expire after 24 hours; use `/users/refresh` with the refresh token to get a new access token
- If tokens are lost, logout and login again to get new ones
- Refresh tokens are stored in the database and can be revoked

### Docker Build Issues
- Ensure Docker daemon is running: `docker ps`
- Check Dockerfile syntax: `docker build --no-cache .`
- View build logs: `docker build . --progress=plain`

## Next Steps

This module completes the back-end logic for the FastAPI Calculator. The next module (Module 13) will add a React frontend to consume these APIs.

## License

MIT License – See LICENSE file for details


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
