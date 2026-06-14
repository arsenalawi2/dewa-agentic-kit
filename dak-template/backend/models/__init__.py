"""Importing this package registers every model on Base.metadata so that
create_all() (dev) and Alembic autogenerate (prod) can see them.

Add new models here — `dak add-model <Name>` appends the import for you.
"""
from models.base import Base  # noqa: F401
from models.item import Item  # noqa: F401
