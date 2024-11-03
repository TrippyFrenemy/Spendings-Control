from app.db.models import async_session
from app.db.models import User, Category, Item
from sqlalchemy import select, update, delete


async def set_user(tg_id: int) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()
