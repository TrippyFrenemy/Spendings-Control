from datetime import datetime
from typing import List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from app.db.models import Expense, Category
from app.db.redis.cache_helpers import invalidate_expense_caches
from app.db.redis.redis_client import redis_cache
from app.db.repositories.category_repository import get_category_by_id


@redis_cache(prefix="expenses_by_date", expire=900)
async def get_expenses_by_date(session: AsyncSession, user_id: int, day: int, month: int, year: int) -> List[Dict]:
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
    expenses = result.scalars().all()

    # Convert to list of dictionaries for JSON serialization
    return [{
        "id": exp.id,
        "user_id": exp.user_id,
        "category_id": exp.category_id,
        "day": exp.day,
        "month": exp.month,
        "year": exp.year,
        "amount": float(exp.amount),
        "description": exp.description,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "category": {
            "id": exp.category.id,
            "name": exp.category.name
        }
    } for exp in expenses]


@redis_cache(prefix="expense", expire=900)
async def get_expense_by_id(session: AsyncSession, expense_id: int) -> Optional[Dict]:
    """Get expense by ID with its category."""
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(Expense.id == expense_id)
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if expense:
        return {
            "id": expense.id,
            "user_id": expense.user_id,
            "category_id": expense.category_id,
            "day": expense.day,
            "month": expense.month,
            "year": expense.year,
            "amount": float(expense.amount),
            "description": expense.description,
            "created_at": expense.created_at.isoformat() if expense.created_at else None,
            "category": {
                "id": expense.category.id,
                "name": expense.category.name,
                "user_id": expense.category.user_id
            } if expense.category else None
        }
    return None


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
async def get_daily_expenses(session: AsyncSession, user_id: int, year: int, month: int) -> List[Dict]:
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
    # Convert to list of dictionaries for JSON serialization
    return [{
        "day": row.day,
        "category": row.category,
        "total": float(row.total)
    } for row in result.all()]


@redis_cache(prefix="monthly_expenses", expire=1800)
async def get_monthly_expenses(session: AsyncSession, user_id: int, year: int, month: int) -> List[Dict]:
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
    # Convert to list of dictionaries for JSON serialization
    return [{
        "category": row.name,
        "total": float(row.total)
    } for row in result.all()]


@redis_cache(prefix="yearly_expenses", expire=3600)
async def get_yearly_expenses(session: AsyncSession, user_id: int, year: int) -> List[Dict]:
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
    # Convert to list of dictionaries for JSON serialization
    return [{
        "month": row.month,
        "category": row.category,
        "total": float(row.total)
    } for row in result.all()]


@redis_cache(prefix="last_expenses", expire=300)
async def get_last_expenses(session: AsyncSession, user_id: int, limit: int = 5) -> List[Dict]:
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
    expenses = result.scalars().all()

    # Convert to list of dictionaries for JSON serialization
    return [{
        "id": exp.id,
        "user_id": exp.user_id,
        "category_id": exp.category_id,
        "day": exp.day,
        "month": exp.month,
        "year": exp.year,
        "amount": float(exp.amount),
        "description": exp.description,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "category": {
            "id": exp.category.id,
            "name": exp.category.name
        }
    } for exp in expenses]


@redis_cache(prefix="unique_years", expire=7200)
async def get_unique_years(session: AsyncSession, user_id: int) -> List[int]:
    """Get all years with expenses for a user."""
    query = select(func.distinct(Expense.year)).where(
        Expense.user_id == user_id
    ).order_by(Expense.year)
    result = await session.execute(query)
    years = [int(year) for year in result.scalars().all()]  # Явно конвертируем в int
    return years if years else [datetime.now().year]


async def update_expense_category(
        session: AsyncSession,
        expense_id: int,
        category_id: int,
        user_id: int
) -> Optional[Dict]:
    """Update expense category and return updated expense."""
    # Get expense with category
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(
        and_(
            Expense.id == expense_id,
            Expense.user_id == user_id
        )
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if not expense:
        return None

    # Store old values for cache invalidation
    year = expense.year
    month = expense.month

    # Update category
    expense.category_id = category_id
    await session.commit()

    # Invalidate caches
    await invalidate_expense_caches(session, user_id, year, month)

    # Return updated expense data
    return {
        "id": expense.id,
        "user_id": expense.user_id,
        "category_id": expense.category_id,
        "day": expense.day,
        "month": expense.month,
        "year": expense.year,
        "amount": float(expense.amount),
        "description": expense.description,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
        "category": {
            "id": expense.category.id,
            "name": expense.category.name
        }
    }


async def delete_expense_by_id(session: AsyncSession, expense_id: int, user_id: int) -> bool:
    """Delete specific expense."""
    query = select(Expense).where(
        and_(
            Expense.id == expense_id,
            Expense.user_id == user_id
        )
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if not expense:
        return False

    # Store year and month before deletion for cache invalidation
    year = expense.year
    month = expense.month

    # Delete the expense
    await session.delete(expense)
    await session.commit()

    # Invalidate related caches
    await invalidate_expense_caches(session, user_id, year, month)
    return True
