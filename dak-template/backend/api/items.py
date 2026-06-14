"""Item CRUD router — the worked example. Mounted at /api/items by app.py.

Shows the DAK request shape: Pydantic in/out models, a session dependency,
and a service call. Copy it with `dak add-model <Name>`.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from services import items as svc

router = APIRouter()


class ItemIn(BaseModel):
    name: str
    note: str = ""


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    note: str


@router.get("", response_model=list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_session)):
    return await svc.list_items(db)


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(body: ItemIn, db: AsyncSession = Depends(get_session)):
    return await svc.create_item(db, body.name, body.note)


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: int, db: AsyncSession = Depends(get_session)):
    item = await svc.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item
