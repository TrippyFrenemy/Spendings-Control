from datetime import datetime
from typing import Optional, List, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import User, Expense, Category
from sqlalchemy import select, func, and_

import logging

logger = logging.getLogger(__name__)


async def get_or_create_user(session: AsyncSession, user_id: int, username: Optional[str] = None) -> User:
    """Get existing user or create new one with default categories."""
    user = await session.get(User, user_id)
    if not user:
        user = User(id=user_id, username=username)
        # Create default categories for new users
        default_categories = ["Продукты", "Бензин", "Кофе", "Рестораны", "Обучение", "Other"]
        for category_name in default_categories:
            category = Category(name=category_name, user_id=user_id)
            session.add(category)
        session.add(user)
        await session.commit()
    return user


async def get_user_categories(session: AsyncSession, user_id: int) -> List[Category]:
    """Get all categories for a user."""
    query = select(Category).where(Category.user_id == user_id).order_by(Category.name)
    result = await session.execute(query)
    return result.scalars().all()


async def get_category_by_id(session: AsyncSession, category_id: int, user_id: int) -> Optional[Category]:
    """Get specific category by ID for a user."""
    query = select(Category).where(
        and_(Category.id == category_id, Category.user_id == user_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def add_category(session: AsyncSession, user_id: int, name: str) -> Category:
    """Add new category for a user."""
    if not name.strip():
        raise ValueError("Category name cannot be empty")

    # Check if category with same name already exists
    existing_query = select(Category).where(
        and_(
            Category.user_id == user_id,
            func.lower(Category.name) == name.strip().lower()
        )
    )
    existing = await session.execute(existing_query)
    if existing.scalar_one_or_none():
        raise ValueError(f"Category '{name}' already exists")

    category = Category(user_id=user_id, name=name.strip())
    session.add(category)
    await session.commit()
    return category


async def update_category(session: AsyncSession, category_id: int, user_id: int, new_name: str) -> Optional[Category]:
    """Update category name."""
    if not new_name.strip():
        raise ValueError("Category name cannot be empty")

    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        return None

    category.name = new_name.strip()
    await session.commit()
    return category


async def delete_category(session: AsyncSession, category_id: int, user_id: int,
                          new_category_id: Optional[int] = None) -> bool:
    """
    Delete category and optionally move its expenses to another category.
    If new_category_id is not provided, expenses will be moved to 'Other' category.
    """
    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        return False

    if new_category_id:
        new_category = await get_category_by_id(session, new_category_id, user_id)
        if not new_category:
            return False
    else:
        # Get or create 'Other' category
        query = select(Category).where(
            and_(Category.user_id == user_id, Category.name == "Other")
        )
        result = await session.execute(query)
        new_category = result.scalar_one_or_none()
        if not new_category:
            new_category = Category(user_id=user_id, name="Other")
            session.add(new_category)
            await session.commit()

    # Move expenses to new category
    query = select(Expense).where(
        and_(Expense.category_id == category_id, Expense.user_id == user_id)
    )
    result = await session.execute(query)
    expenses = result.scalars().all()

    for expense in expenses:
        expense.category_id = new_category.id

    await session.delete(category)
    await session.commit()
    return True


async def add_expense(session: AsyncSession, user_id: int, day: int, month: int, year: int,
                      amount: float, category_id: int, description: Optional[str] = None) -> Expense:
    """Add new expense with category and optional description."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    # Verify category exists and belongs to user
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
    return expense


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


async def get_expense_by_id(session: AsyncSession, expense_id: int) -> Optional[Expense]:
    """Get expense by ID with its category."""
    query = select(Expense).options(
        joinedload(Expense.category)
    ).where(Expense.id == expense_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


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


async def get_category_statistics(session: AsyncSession, user_id: int, category_id: int) -> Dict:
    """Get statistics for a specific category."""
    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        raise ValueError("Invalid category")

    # Get total spent in category
    total_query = select(func.sum(Expense.amount)).where(
        and_(
            Expense.user_id == user_id,
            Expense.category_id == category_id
        )
    )
    total_result = await session.execute(total_query)
    total_spent = total_result.scalar() or 0.0

    # Get number of expenses in category
    count_query = select(func.count()).where(
        and_(
            Expense.user_id == user_id,
            Expense.category_id == category_id
        )
    )
    count_result = await session.execute(count_query)
    expense_count = count_result.scalar() or 0

    # Get average expense in category
    avg_amount = total_spent / expense_count if expense_count > 0 else 0

    return {
        "name": category.name,
        "total_spent": total_spent,
        "expense_count": expense_count,
        "average_amount": avg_amount
    }


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
    query = select(Expense).where(
        and_(
            Expense.id == expense_id,
            Expense.user_id == user_id
        )
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if expense:
        await session.delete(expense)
        await session.commit()
        return True
    return False


async def get_total_spent(session: AsyncSession, user_id: int) -> float:
    """Get total amount spent by user."""
    query = select(func.sum(Expense.amount)).where(Expense.user_id == user_id)
    result = await session.execute(query)
    return result.scalar() or 0.0
