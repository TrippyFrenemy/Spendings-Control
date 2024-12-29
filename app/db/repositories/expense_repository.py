from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from app.db.models import Expense, Category
from app.db.redis.cache_helpers import invalidate_expense_caches
from app.db.redis.redis_client import redis_cache
from app.db.repositories.category_repository import get_category_by_id


@redis_cache(prefix="expenses_by_date", expire=900)
async def get_expenses_by_date(session: AsyncSession, user_id: int, day: int, month: int, year: int) -> List[Expense]:
    """Get all expenses for a specific date with their categories."""
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(
        and_(
            Expense.user_id == user_id,
            Expense.day == day,
            Expense.month == month,
            Expense.year == year
        )
    )
    result = await session.execute(query)
    return result.scalars().all()


@redis_cache(prefix="expense", expire=900)
async def get_expense_by_id(session: AsyncSession, expense_id: int) -> Optional[Expense]:
    """Get expense by ID with its category."""
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(Expense.id == expense_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def add_expense(session: AsyncSession, user_id: int, day: int, month: int, year: int,
                     amount: float, category_id: int, description: Optional[str] = None) -> Expense:
    """Add new expense with category and optional description."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        raise ValueError("Invalid category")

    expense = Expense(
        user_id=user_id,
        day=day,
        month=month,
        year=year,
        amount=amount,
        category_id=category_id,
        description=description.strip() if description else None
    )
    session.add(expense)
    await session.commit()

    # Invalidate related caches
    await invalidate_expense_caches(session, user_id, year, month)
    return expense


@redis_cache(prefix="daily_expenses", expire=900)
async def get_daily_expenses(session: AsyncSession, user_id: int, year: int, month: int) -> List[Tuple[int, str, float]]:
    """Get daily expenses by category for a specific month."""
    query = select(
        Expense.day,
        Category.name.label('category'),
        func.sum(Expense.amount).label('total')
    ).join(Category).where(
        and_(
            Expense.user_id == user_id,
            Expense.year == year,
            Expense.month == month
        )
    ).group_by(
        Expense.day,
        Category.name
    ).order_by(
        Expense.day.asc(),
        Category.name.asc()
    )

    result = await session.execute(query)
    return result.all()


@redis_cache(prefix="monthly_expenses", expire=1800)
async def get_monthly_expenses(session: AsyncSession, user_id: int, year: int, month: int) -> List[Tuple[str, float]]:
    """Get total expenses by category for a specific month."""
    query = select(
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(Category).where(
        and_(
            Expense.user_id == user_id,
            Expense.year == year,
            Expense.month == month
        )
    ).group_by(Category.name)

    result = await session.execute(query)
    return result.all()


@redis_cache(prefix="yearly_expenses", expire=3600)
async def get_yearly_expenses(session: AsyncSession, user_id: int, year: int) -> List[Tuple[int, str, float]]:
    """Get monthly expenses by category for a specific year."""
    query = select(
        Expense.month,
        Category.name.label('category'),
        func.sum(Expense.amount).label('total')
    ).join(Category).where(
        and_(
            Expense.user_id == user_id,
            Expense.year == year
        )
    ).group_by(
        Expense.month,
        Category.name
    ).order_by(
        Expense.month.asc(),
        Category.name.asc()
    )

    result = await session.execute(query)
    return result.all()


@redis_cache(prefix="last_expenses", expire=300)
async def get_last_expenses(session: AsyncSession, user_id: int, limit: int = 5) -> List[Expense]:
    """Get last expenses with their categories."""
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(
        Expense.user_id == user_id
    ).order_by(
        Expense.year.desc(),
        Expense.month.desc(),
        Expense.day.desc()
    ).limit(limit)

    result = await session.execute(query)
    return result.scalars().all()


@redis_cache(prefix="unique_years", expire=7200)
async def get_unique_years(session: AsyncSession, user_id: int) -> List[int]:
    """Get all years with expenses for a user."""
    query = select(func.distinct(Expense.year)).where(
        Expense.user_id == user_id
    ).order_by(Expense.year)
    result = await session.execute(query)
    years = result.scalars().all()
    return years if years else [datetime.now().year]


async def delete_expense_by_id(session: AsyncSession, expense_id: int, user_id: int) -> bool:
    """Delete specific expense."""
    expense = await get_expense_by_id(session, expense_id)
    if not expense or expense.user_id != user_id:
        return False

    await session.delete(expense)
    await session.commit()

    # Invalidate related caches
    await invalidate_expense_caches(session, user_id, expense.year, expense.month)
    return True
