from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import BigInteger, Integer, String, ForeignKey, Float, DateTime, Column, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DB_DRIVER, DB_USER, DB_PASS, DB_HOST, DB_NAME

engine = create_async_engine(url=f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)  # Telegram user id
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    day = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_expense_user_year', 'user_id', 'year'),
        Index('idx_expense_user_year_month', 'user_id', 'year', 'month'),
        Index('idx_expense_date', 'user_id', 'year', 'month', 'day'),
    )


async def async_main():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Properly handles session creation and cleanup.

    Usage:
        async with get_async_session() as session:
            # Use session here
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
