from typing import List, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.models import Income
from app.db.redis.redis_client import redis_cache
from app.db.redis.cache_helpers import invalidate_income_caches


@redis_cache(prefix="last_incomes", expire=300)
async def get_last_incomes(session: AsyncSession, user_id: int, limit: int = 5) -> List[Dict]:
    """Get last recorded incomes."""
    query = select(Income).where(
        Income.user_id == user_id
    ).order_by(
        Income.year.desc(),
        Income.month.desc(),
        Income.day.desc()
    ).limit(limit)

    result = await session.execute(query)
    incomes = result.scalars().all()

    return [{
        "id": inc.id,
        "user_id": inc.user_id,
        "day": inc.day,
        "month": inc.month,
        "year": inc.year,
        "amount": float(inc.amount),
        "description": inc.description,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
    } for inc in incomes]


@redis_cache(prefix="total_income", expire=1800)
async def get_total_income(session: AsyncSession, user_id: int) -> float:
    """Get total amount of recorded incomes for a user."""
    query = select(func.sum(Income.amount)).where(Income.user_id == user_id)
    result = await session.execute(query)
    return float(result.scalar() or 0.0)


async def add_income(
    session: AsyncSession,
    user_id: int,
    day: int,
    month: int,
    year: int,
    amount: float,
    description: Optional[str] = None,
) -> Income:
    """Add a new income entry."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    income = Income(
        user_id=user_id,
        day=day,
        month=month,
        year=year,
        amount=amount,
        description=description.strip() if description else None,
    )
    session.add(income)
    await session.commit()

    await invalidate_income_caches(session, user_id, year, month)
    return income


@redis_cache(prefix="incomes_by_date", expire=900)
async def get_incomes_by_date(
    session: AsyncSession,
    user_id: int,
    day: int,
    month: int,
    year: int,
) -> List[Dict]:
    """Get all incomes for a specific date."""
    query = select(Income).where(
        and_(
            Income.user_id == user_id,
            Income.day == day,
            Income.month == month,
            Income.year == year,
        )
    )
    result = await session.execute(query)
    incomes = result.scalars().all()
    return [
        {
            "id": inc.id,
            "user_id": inc.user_id,
            "day": inc.day,
            "month": inc.month,
            "year": inc.year,
            "amount": float(inc.amount),
            "description": inc.description,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
        }
        for inc in incomes
    ]


async def delete_income_by_id(session: AsyncSession, income_id: int, user_id: int) -> bool:
    """Delete specific income."""
    query = select(Income).where(
        and_(
            Income.id == income_id,
            Income.user_id == user_id,
        )
    )
    result = await session.execute(query)
    income = result.scalar_one_or_none()

    if not income:
        return False

    year = income.year
    month = income.month

    await session.delete(income)
    await session.commit()

    await invalidate_income_caches(session, user_id, year, month)
    return True


@redis_cache(prefix="daily_income", expire=900)
async def get_daily_incomes(
    session: AsyncSession, user_id: int, year: int, month: int
) -> List[Dict]:
    """Get total incomes per day for a specific month."""
    query = (
        select(Income.day, func.sum(Income.amount).label("total"))
        .where(
            and_(
                Income.user_id == user_id,
                Income.year == year,
                Income.month == month,
            )
        )
        .group_by(Income.day)
        .order_by(Income.day.asc())
    )
    result = await session.execute(query)
    return [
        {"day": row.day, "total": float(row.total)} for row in result.all()
    ]


@redis_cache(prefix="monthly_income", expire=1800)
async def get_monthly_incomes(
    session: AsyncSession, user_id: int, year: int
) -> List[Dict]:
    """Get total incomes per month for a specific year."""
    query = (
        select(Income.month, func.sum(Income.amount).label("total"))
        .where(and_(Income.user_id == user_id, Income.year == year))
        .group_by(Income.month)
        .order_by(Income.month.asc())
    )
    result = await session.execute(query)
    return [
        {"month": row.month, "total": float(row.total)} for row in result.all()
    ]
