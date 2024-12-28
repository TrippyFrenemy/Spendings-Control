import logging

from aiogram import types

from app.db.models import get_async_session
from app.db.repositories.user_repository import get_or_create_user
from app.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)


async def cmd_start(message: types.Message) -> None:
    async with get_async_session() as session:
        await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username
        )

    await message.answer(
        'Welcome to the Expense Tracker Bot!\n\n'
        'To record an expense, use either format:\n'
        '1. DD.MM.YY amount description\n'
        '2. amount description (uses today\'s date)\n\n'
        'Examples:\n'
        '26.12.24 500 coffee with friends\n'
        '500 coffee with friends\n\n'
        'You\'ll then be prompted to select a category for the expense.\n\n'
        'Use the keyboard below to access reports and manage your expenses.',
        reply_markup=get_main_keyboard()
    )