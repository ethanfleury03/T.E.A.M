"""Pytest fixtures: isolated SQLite DB per test (no real pantry.db)."""

from __future__ import annotations

import pytest

import database as db


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Point the app database at a temporary file and re-initialize schema."""
    db_path = tmp_path / "test_pantry.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(db, "_db_initialized", False)
    conn = getattr(db._local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        finally:
            del db._local.conn
    db.init_db()
    yield db_path
    conn = getattr(db._local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        finally:
            del db._local.conn
