PR: Complete Backend Implementation - User & Calculation BREAD Endpoints (Module 12)

Summary:
This PR completes the FastAPI Calculator backend with full user management and calculation BREAD endpoints.

**New Features:**
- ✅ User Registration (POST /users/register)
- ✅ User Login with JWT tokens (POST /users/login)
- ✅ Calculation BREAD Endpoints:
  - Browse: GET /calculations (list all with pagination)
  - Read: GET /calculations/{id}
  - Edit: PUT /calculations/{id}
  - Add: POST /calculations
  - Delete: DELETE /calculations/{id}
- ✅ JWT Access & Refresh Tokens with server-side storage
- ✅ User token management and revocation
- ✅ Admin role and privileged endpoints
- ✅ Comprehensive integration tests (pytest with PostgreSQL support)
- ✅ GitHub Actions CI/CD pipeline with Docker Hub integration
- ✅ Alembic database migrations

**Testing:**
- ✅ All 20 tests pass locally with 83% code coverage
- ✅ Integration tests cover:
  - User registration/login flow
  - Token refresh and logout
  - Calculation CRUD operations
  - Invalid input validation
  - Division by zero prevention
  - Admin token management

**CI/CD:**
- ✅ GitHub Actions workflow (ci.yml):
  - Runs tests on every push and PR
  - Spins up PostgreSQL service for integration tests
  - Builds and pushes Docker image to Docker Hub on success
  - Optional Slack notifications
- ✅ Release workflow for git tags

**Documentation:**
- ✅ Updated README with:
  - Full API endpoint documentation
  - User registration/login examples
  - Calculation CRUD examples
  - Testing instructions
  - Docker setup and deployment guide
  - Troubleshooting section

**Environment Setup Required:**
To enable Docker Hub integration in CI, configure GitHub Secrets:
- `DOCKERHUB_USERNAME` – Your Docker Hub username
- `DOCKERHUB_TOKEN` – Docker Hub Personal Access Token
- `DOCKER_HUB_REPO` – Full Docker Hub repo (e.g., username/fastapi-calculator)

**Running Locally:**
```powershell
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Run tests
pytest --cov=app --cov-report=term-missing
```

**Next Steps (Module 13):**
- Add React frontend to consume the API
- Connect calculation endpoints to user accounts
- Implement frontend authentication flow

