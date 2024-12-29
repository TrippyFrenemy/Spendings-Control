from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.models import Category, Expense
from app.db.redis.cache_helpers import invalidate_expense_caches
from app.db.redis.redis_client import redis_cache


@redis_cache(prefix="categories", expire=3600)
async def get_user_categories(session: AsyncSession, user_id: int) -> List[Category]:
    """Get all categories for a user."""
    query = select(Category).where(Category.user_id == user_id).order_by(Category.name)
    result = await session.execute(query)
    return result.scalars().all()


@redis_cache(prefix="category", expire=1800)
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

    # Invalidate caches
    await get_user_categories.invalidate_cache(session, user_id)
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

    # Invalidate caches
    await get_user_categories.invalidate_cache(session, user_id)
    await get_category_by_id.invalidate_cache(session, category_id, user_id)
    return category


async def delete_category(session: AsyncSession, category_id: int, user_id: int,
                          new_category_id: Optional[int] = None) -> bool:
    """Delete category and optionally move its expenses to another category."""
    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        return False

    if new_category_id:
        new_category = await get_category_by_id(session, new_category_id, user_id)
        if not new_category:
            return False
    else:
        query = select(Category).where(
            and_(Category.user_id == user_id, Category.name == "Other")
        )
        result = await session.execute(query)
        new_category = result.scalar_one_or_none()
        if not new_category:
            new_category = Category(user_id=user_id, name="Other")
            session.add(new_category)
            await session.commit()

    query = select(Expense).where(
        and_(Expense.category_id == category_id, Expense.user_id == user_id)
    )
    result = await session.execute(query)
    expenses = result.scalars().all()

    for expense in expenses:
        expense.category_id = new_category.id

    await session.delete(category)
    await session.commit()

    # Invalidate all related caches
    await get_user_categories.invalidate_cache(session, user_id)
    await get_category_by_id.invalidate_cache(session, category_id, user_id)
    await invalidate_expense_caches(session, user_id)
    return True


@redis_cache(prefix="category_stats", expire=1800)
async def get_category_statistics(session: AsyncSession, user_id: int, category_id: int) -> Dict:
    """Get statistics for a specific category."""
    category = await get_category_by_id(session, category_id, user_id)
    if not category:
        raise ValueError("Invalid category")

    total_query = select(func.sum(Expense.amount)).where(
        and_(
            Expense.user_id == user_id,
            Expense.category_id == category_id
        )
    )
    total_result = await session.execute(total_query)
    total_spent = total_result.scalar() or 0.0

    count_query = select(func.count()).where(
        and_(
            Expense.user_id == user_id,
            Expense.category_id == category_id
        )
    )
    count_result = await session.execute(count_query)
    expense_count = count_result.scalar() or 0

    avg_amount = total_spent / expense_count if expense_count > 0 else 0

    return {
        "name": category.name,
        "total_spent": total_spent,
        "expense_count": expense_count,
        "average_amount": avg_amount
    }
