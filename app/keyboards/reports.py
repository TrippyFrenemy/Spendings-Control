from datetime import datetime
import calendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.db.models import get_async_session
from app.db.repositories.expense_repository import get_unique_years


async def create_year_keyboard(user_id: int, report_type: str = "monthly") -> InlineKeyboardMarkup:
    """Creates an inline keyboard with available years for reports."""
    async with get_async_session() as session:
        years = await get_unique_years(session, user_id)
        if not years:
            years = [datetime.now().year]

        buttons = [[InlineKeyboardButton(
            text=str(year),
            callback_data=f"year_{year}_{report_type}"
        )] for year in years]

        return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_month_keyboard(year: int, report_type: str = "monthly") -> InlineKeyboardMarkup:
    """Creates an inline keyboard with months for reports."""
    current_year = datetime.now().year
    current_month = datetime.now().month

    buttons = []
    for month in range(1, 13):
        if year == current_year and month > current_month:
            continue
        month_name = calendar.month_abbr[month]
        callback_data = (
            f"daily_month_{year}_{month}" if report_type == "daily"
            else f"month_{year}_{month}"
        )
        buttons.append([InlineKeyboardButton(
            text=month_name,
            callback_data=callback_data
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ Back to years",
        callback_data="back_to_years"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
