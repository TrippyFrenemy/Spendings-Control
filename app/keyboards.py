from datetime import datetime
import calendar
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from app.db.models import get_async_session
from app.db.requests import get_unique_years


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates the main keyboard with expense tracking options.
    Returns a ReplyKeyboardMarkup with all main bot functions.
    """
    keyboard = [
        [KeyboardButton(text='📊 Monthly Report'), KeyboardButton(text='📅 Yearly Report')],
        [KeyboardButton(text='💰 Total Spent')],
        [KeyboardButton(text='🔍 Last 5 Expenses'), KeyboardButton(text='❌ Delete Expense')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def create_year_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with available years for the user.
    If no expenses exist, returns current year as the only option.
    """
    async with get_async_session() as session:
        years = await get_unique_years(session, user_id)
        if not years:
            years = [datetime.now().year]

        buttons = [[InlineKeyboardButton(
            text=str(year),
            callback_data=f"year_{year}"
        )] for year in years]

        return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_month_keyboard(year: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with months.
    For current year, only shows months up to current month.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    buttons = []
    for month in range(1, 13):
        if year == current_year and month > current_month:
            continue
        month_name = calendar.month_abbr[month]
        buttons.append([InlineKeyboardButton(
            text=month_name,
            callback_data=f"month_{year}_{month}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ Back to years",
        callback_data="back_to_years"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_confirmation_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """
    Creates a confirmation keyboard for expense deletion.
    """
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"del_{expense_id}_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"del_{expense_id}_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)