import os
import importlib

from sqlalchemy.orm import Session
import sqlalchemy

import app.database as database


def test_get_db_yields_session_and_closes():
    # use the default engine (sqlite) to exercise get_db()
    gen = database.get_db()
    db = next(gen)

    assert isinstance(db, Session)

    # exhausting the generator should trigger the "finally: db.close()"
    try:
        next(gen)
    except StopIteration:
        pass


def test_database_else_branch_with_non_sqlite_url(monkeypatch):
    """
    Force DATABASE_URL to be non-sqlite so the `else:` branch in app.database
    runs, but patch create_engine so we don't need a real Postgres server.
    """
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/somedb"

    original_create_engine = sqlalchemy.create_engine

    def fake_create_engine(url, *args, **kwargs):
        # We just want these lines to execute; use in-memory sqlite underneath.
        return original_create_engine("sqlite:///:memory:", *args, **kwargs)

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

    import app.database as db_module
    importlib.reload(db_module)

    # confirm it picked up the non-sqlite URL (so the else-branch ran)
    assert db_module.SQLALCHEMY_DATABASE_URL.startswith("postgresql://")

    # cleanup
    os.environ.pop("DATABASE_URL", None)
