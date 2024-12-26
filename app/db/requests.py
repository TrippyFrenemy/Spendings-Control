from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Expense
from sqlalchemy import select, func

import logging


async def get_or_create_user(session: AsyncSession, user_id: int, username: Optional[str] = None) -> User:
    user = await session.get(User, user_id)
    if not user:
        user = User(id=user_id, username=username)
        session.add(user)
        await session.commit()
    return user


async def add_expense(session: AsyncSession, user_id: int, day: int, month: int, year: int, amount: float,
                      category: str) -> Expense:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if not category.strip():
        raise ValueError("Category cannot be empty")

    expense = Expense(
        user_id=user_id,
        day=day,
        month=month,
        year=year,
        amount=amount,
        category=category
    )
    session.add(expense)
    await session.commit()
    return expense


async def get_expenses_by_date(session: AsyncSession, user_id: int ,day: int ,month: int ,year: int) -> List[Expense]:
    query = select(Expense).where(
        Expense.user_id == user_id,
        Expense.day == day,
        Expense.month == month,
        Expense.year == year
    )
    result = await session.execute(query)
    return result.scalars().all()


async def get_monthly_expenses(session: AsyncSession, user_id: int, year: int, month: int) -> List[Tuple[str, float]]:
    # Если передан двузначный год, преобразуем его в четырехзначный
    if year < 100:
        year = 2000 + year

    query = select(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).where(
        Expense.user_id == user_id,
        Expense.year == year,
        Expense.month == month
    ).group_by(Expense.category)

    result = await session.execute(query)
    return result.all()


async def get_yearly_expenses(session: AsyncSession, user_id: int, year: int) -> List[Tuple[int, str, float]]:
    # Add year conversion for two-digit years
    if year < 100:
        year = 2000 + year

    # First, let's add logging to understand what we're querying
    logging.info(f"Getting yearly expenses for user {user_id} and year {year}")

    # First check if we have any data for this year
    check_query = select(func.count()).select_from(Expense).where(
        Expense.user_id == user_id,
        Expense.year == year
    )
    count = await session.execute(check_query)
    count_result = count.scalar()
    logging.info(f"Found {count_result} records for year {year}")

    # Modify the main query to ensure proper grouping and ordering
    query = select(
        Expense.month,
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).where(
        Expense.user_id == user_id,
        Expense.year == year
    ).group_by(
        Expense.month,
        Expense.category
    ).order_by(
        Expense.month.asc(),  # Explicit ordering
        Expense.category.asc()
    )

    # Execute query and get results
    result = await session.execute(query)
    data = result.all()
    logging.info(f"Query returned {len(data)} grouped results")

    # If we have no grouped results but we know we have records, there might be an issue
    if not data and count_result > 0:
        logging.warning("Found records but grouping returned no results")

        # Let's try to get raw data for debugging
        raw_query = select(Expense).where(
            Expense.user_id == user_id,
            Expense.year == year
        )
        raw_result = await session.execute(raw_query)
        raw_data = raw_result.scalars().all()
        logging.info(f"Raw data sample: {raw_data[:3] if raw_data else 'No raw data'}")

    return data


async def get_last_expenses(session: AsyncSession, user_id: int, limit: int = 5) -> List[Expense]:
    query = select(Expense).where(
        Expense.user_id == user_id
    ).order_by(
        Expense.year.desc(),
        Expense.month.desc(),
        Expense.day.desc()
    ).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_unique_years(session: AsyncSession, user_id: int) -> List[int]:
    query = select(func.distinct(Expense.year)).where(
        Expense.user_id == user_id
    ).order_by(Expense.year)
    result = await session.execute(query)
    years = result.scalars().all()
    return years if years else [datetime.now().year]


async def delete_expense_by_id(session: AsyncSession, expense_id: int, user_id: int) -> bool:
    query = select(Expense).where(
        Expense.id == expense_id,
        Expense.user_id == user_id
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if expense:
        await session.delete(expense)
        await session.commit()
        return True
    return False


async def get_total_spent(session: AsyncSession, user_id: int) -> float:
    query = select(func.sum(Expense.amount)).where(Expense.user_id == user_id)
    result = await session.execute(query)
    return result.scalar() or 0.0
