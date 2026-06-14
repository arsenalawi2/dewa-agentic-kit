"""Test fixtures.

Points the app at a throwaway SQLite file *before* importing it (database.py
reads DATABASE_URL at import time), so tests need no Postgres. The app's
lifespan creates the tables on startup (DAK_AUTO_CREATE=1).
"""
import os
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp.name}"
os.environ.setdefault("DAK_AUTO_CREATE", "1")
os.environ.setdefault("DETAILED_PASSWORD", "test-password")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    from app import app

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
