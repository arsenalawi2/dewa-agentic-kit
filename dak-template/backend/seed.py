"""Seed example data:  python -m seed   (run in backend/ or the container).

Idempotent — does nothing if items already exist. Use it as the shape for
your own seed routines.
"""
import asyncio

import models  # noqa: F401 — registers models on Base.metadata
from database import SessionLocal, engine
from models.base import Base
from services import items as svc


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if await svc.list_items(db):
            print("seed: items already present — nothing to do")
            return
        for name in ("First item", "Second item"):
            await svc.create_item(db, name, note="seeded example")
        print("seed: inserted 2 example items")


if __name__ == "__main__":
    asyncio.run(main())
