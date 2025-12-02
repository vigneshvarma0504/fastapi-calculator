PR: Add token management, roles, Alembic scaffold, and admin endpoints

Summary:
- Implement JWT access and refresh tokens with server-side RefreshToken storage.
- Add endpoints for token issuance, refresh, revocation, and admin token management.
- Add user roles and admin-only endpoints (user role management, token listing, revoke-all, revoke-by-token).
- Add Alembic scaffold and initial migration `0001_initial.py` for SQLite/Postgres.
- Add OpenAPI `bearerAuth` security scheme for clearer /docs UI.

Testing:
- All tests pass locally: `20 passed`.

Notes:
- Set `SECRET_KEY`, `DOCKER_HUB_REPO`, and GitHub Secrets for CI/Docker push.
- Alembic scaffold included; run `alembic upgrade head` after setting `DATABASE_URL`.
