"""SQLAlchemy declarative base.

Every ORM model inherits from Base, so Base.metadata knows about every
table — that's what create_all (dev, see database.py) and Alembic
(prod) use to build the schema.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
