"""Item data-access logic — no HTTP here (that lives in api/items.py)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.item import Item


async def list_items(db: AsyncSession) -> list[Item]:
    res = await db.execute(select(Item).order_by(Item.created_at.desc()))
    return list(res.scalars().all())


async def create_item(db: AsyncSession, name: str, note: str = "") -> Item:
    item = Item(name=name, note=note)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    return await db.get(Item, item_id)
