import logging
from datetime import datetime
from aiogram import types

from app.db.models import get_async_session
from app.db.repositories.expense_repository import add_expense
from app.db.repositories.category_repository import get_user_categories
from app.keyboards import create_category_selection_keyboard

logger = logging.getLogger(__name__)


def parse_date_from_text(parts: list) -> datetime:
    """Parse date from message parts."""
    try:
        date = datetime.strptime(parts[0], '%d.%m.%y')
        return date
    except ValueError:
        return datetime.now()


def parse_amount_and_description(parts: list, has_date: bool) -> tuple:
    """Parse amount and description based on whether date was provided."""
    if has_date:
        amount = float(parts[1])
        description = parts[2] if len(parts) > 2 else None
    else:
        amount = float(parts[0])
        description = parts[1] if len(parts) > 1 else None
    return amount, description


def create_expense_data(date: datetime, amount: float, description: str = None) -> str:
    """Create expense data string for callback."""
    year = 2000 + date.year % 100
    expense_data = f"{date.day},{date.month},{year},{amount}"
    if description:
        expense_data += f",{description}"
    return expense_data


async def handle_expense(message: types.Message) -> None:
    """Default handler that processes expense entries."""
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2:
            raise ValueError("Not enough arguments")

        date = parse_date_from_text(parts)
        amount, description = parse_amount_and_description(parts, date is not None)
        expense_data = create_expense_data(date, amount, description)

        keyboard = await create_category_selection_keyboard(message.from_user.id, expense_data)
        await message.answer(
            "Please select a category for your expense:",
            reply_markup=keyboard
        )

    except ValueError as e:
        logger.error(f"Value error in handle_expense: {e}")
        await message.answer(
            "❌ Invalid format. Please use either:\n"
            "1. DD.MM.YY amount description\n"
            "2. amount description\n"
            "Examples:\n"
            "26.12.23 500 coffee with friends\n"
            "500 coffee with friends"
        )
    except Exception as e:
        logger.error(f"Unexpected error in handle_expense: {e}")
        await message.answer("❌ An error occurred while recording the expense")


async def process_category_selection(callback: types.CallbackQuery) -> None:
    """Handles category selection for an expense."""
    try:
        _, category_id, *expense_data = callback.data.split('_')
        category_id = int(category_id)
        expense_data = expense_data[0].split(',')

        day, month, year = map(int, expense_data[:3])
        amount = float(expense_data[3])
        description = expense_data[4] if len(expense_data) > 4 else None

        async with get_async_session() as session:
            expense = await add_expense(
                session,
                callback.from_user.id,
                day, month, year,
                amount,
                category_id,
                description
            )

            categories = await get_user_categories(session, callback.from_user.id)
            category_name = next(cat.name for cat in categories if cat.id == category_id)

            message = f"✅ Recorded: {amount:.2f} UAH"
            if description:
                message += f" for {description}"
            message += f"\nCategory: {category_name}\nDate: {day:02d}.{month:02d}.{year}"

            await callback.message.edit_text(message)

    except Exception as e:
        logger.error(f"Error in process_category_selection: {e}")
        await callback.message.edit_text("❌ An error occurred while categorizing the expense")
