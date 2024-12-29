from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.redis.redis_client import redis
from app.db.redis.report_image_cache import invalidate_report_images


async def invalidate_expense_caches(session: AsyncSession, user_id: int, year: Optional[int] = None,
                                    month: Optional[int] = None):
    """Invalidate all expense-related caches for a user."""
    # Build patterns for cache keys to delete
    patterns = [
        f"total_spent:*{user_id}*",  # Total spent cache
        f"unique_years:*{user_id}*",  # Years cache
        f"last_expenses:*{user_id}*",  # Last expenses cache
    ]

    if year:
        patterns.extend([
            f"yearly_expenses:*{user_id}*{year}*",  # Yearly expenses cache
        ])
        if month:
            patterns.extend([
                f"monthly_expenses:*{user_id}*{year}*{month}*",  # Monthly expenses cache
                f"daily_expenses:*{user_id}*{year}*{month}*",  # Daily expenses cache
                f"expenses_by_date:*{user_id}*{year}*{month}*"  # Expenses by date cache
            ])

    # Delete all matching keys
    for pattern in patterns:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)

    # Also invalidate report images
    await invalidate_report_images(user_id, year, month)


async def invalidate_category_caches(session: AsyncSession, user_id: int):
    """Invalidate all category-related caches for a user."""
    patterns = [
        f"categories:*{user_id}*",  # User categories list
        f"category:*{user_id}*",  # Individual category data
        f"category_stats:*{user_id}*"  # Category statistics
    ]

    for pattern in patterns:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)


async def invalidate_all_user_caches(session: AsyncSession, user_id: int):
    """Invalidate all caches for a specific user."""
    patterns = [
        f"*{user_id}*"  # All user related caches
    ]

    for pattern in patterns:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
