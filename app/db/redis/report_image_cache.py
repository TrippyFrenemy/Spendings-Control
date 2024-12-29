from typing import Optional
from app.db.redis.redis_client import redis

# Constants for different report types
DAILY_REPORT = "daily"
MONTHLY_REPORT = "monthly"
YEARLY_REPORT = "yearly"


def get_image_key(report_type: str, user_id: int, year: int, month: Optional[int] = None) -> str:
    """Generate Redis key for report image."""
    if month is not None:
        return f"report_image:{report_type}:{user_id}:{year}:{month}"
    return f"report_image:{report_type}:{user_id}:{year}"


async def cache_report_image(
        report_type: str,
        user_id: int,
        year: int,
        month: Optional[int],
        image_bytes: bytes,
        expire: int = 900  # 15 minutes default
) -> None:
    """Cache report image in Redis."""
    key = get_image_key(report_type, user_id, year, month)
    await redis.set(key, image_bytes, ex=expire)


async def get_cached_report_image(
        report_type: str,
        user_id: int,
        year: int,
        month: Optional[int] = None
) -> Optional[bytes]:
    """Get cached report image from Redis."""
    key = get_image_key(report_type, user_id, year, month)
    return await redis.get(key)


async def invalidate_report_images(user_id: int, year: Optional[int] = None, month: Optional[int] = None):
    """Invalidate report images based on parameters."""
    patterns = []

    if year is None:
        # If no year specified, invalidate all user's report images
        patterns.append(f"report_image:*:{user_id}:*")
    elif month is None:
        # If year specified but no month, invalidate all reports for that year
        patterns.append(f"report_image:*:{user_id}:{year}:*")
        patterns.append(f"report_image:yearly:{user_id}:{year}")
    else:
        # If both year and month specified, invalidate specific monthly and daily reports
        patterns.append(f"report_image:daily:{user_id}:{year}:{month}")
        patterns.append(f"report_image:monthly:{user_id}:{year}:{month}")
        patterns.append(f"report_image:yearly:{user_id}:{year}")

    for pattern in patterns:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
