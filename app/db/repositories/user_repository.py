from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import User, Category, Expense
from app.db.repositories.category_repository import get_user_categories
from app.db.redis.redis_client import redis_cache


@redis_cache(prefix="user", expire=3600)
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

        # Invalidate user categories cache
        await get_user_categories.invalidate_cache(session, user_id)
    return user


@redis_cache(prefix="total_spent", expire=1800)
async def get_total_spent(session: AsyncSession, user_id: int) -> float:
    """Get total amount spent by user."""
    query = select(func.sum(Expense.amount)).where(Expense.user_id == user_id)
    result = await session.execute(query)
    return result.scalar() or 0.0
