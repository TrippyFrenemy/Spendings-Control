from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import BigInteger, Integer, String, ForeignKey, Float, DateTime, Column, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import relationship

from config import DB_DRIVER, DB_USER, DB_PASS, DB_HOST, DB_NAME

engine = create_async_engine(url=f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)  # Telegram user id
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    categories = relationship("Category", back_populates="user")
    incomes = relationship("Income", back_populates="user")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")

    __table_args__ = (
        Index('idx_category_user', 'user_id'),
    )


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    day = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)  # Optional description field
    created_at = Column(DateTime, default=datetime.now)

    category = relationship("Category", back_populates="expenses")

    __table_args__ = (
        Index('idx_expense_user_year', 'user_id', 'year'),
        Index('idx_expense_user_year_month', 'user_id', 'year', 'month'),
        Index('idx_expense_date', 'user_id', 'year', 'month', 'day'),
    )


class Income(Base):
    __tablename__ = 'incomes'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    day = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="incomes")

    __table_args__ = (
        Index('idx_income_user_year', 'user_id', 'year'),
        Index('idx_income_user_year_month', 'user_id', 'year', 'month'),
        Index('idx_income_date', 'user_id', 'year', 'month', 'day'),
    )


async def async_main():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Properly handles session creation and cleanup.
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
