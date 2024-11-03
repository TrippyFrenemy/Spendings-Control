from datetime import datetime

from sqlalchemy import BigInteger, Integer, String, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3")

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, unique=True)


class Category(Base):
    __tablename__ = "categories"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String(50), unique=True)


class Item(Base):
    __tablename__ = "items"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    description = mapped_column(String(150))
    amount = mapped_column(Float, default=0.0)
    date = mapped_column(DateTime)
    category_id = mapped_column(Integer, ForeignKey("categories.id"))
    type = mapped_column(Boolean)
    user_id = mapped_column(Integer, ForeignKey("users.id"))


async def async_main():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)
