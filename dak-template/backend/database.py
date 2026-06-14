"""Async SQLAlchemy 2 session manager — DAK default.

Uses asyncpg for Postgres. For local-only SQLite tools, swap the URL
to `sqlite+aiosqlite:///./app.db`.

Usage in routes:
    from database import get_session

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_session)):
        ...
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/app",
)

engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def db_ping() -> bool:
    """Used by /readyz."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))  # SQLAlchemy 2 needs text()
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan — runs once on startup/shutdown.

    In dev (DAK_AUTO_CREATE=1, the default) any missing tables are created on
    boot, so a fresh project has a working schema immediately. In prod, set
    DAK_AUTO_CREATE=0 and manage the schema with Alembic instead.
    """
    if os.environ.get("DAK_AUTO_CREATE", "1") == "1":
        try:
            import models  # noqa: F401 — registers every model on Base.metadata
            from models.base import Base

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception:
            logging.getLogger("app").exception("create_all failed; continuing without it")
    yield
    await engine.dispose()
