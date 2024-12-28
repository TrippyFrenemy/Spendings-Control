from datetime import datetime
import calendar
from typing import List

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from app.db.models import get_async_session, Category
from app.db.requests import get_unique_years, get_user_categories


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates the main keyboard with expense tracking options.
    Returns a ReplyKeyboardMarkup with all main bot functions.
    """
    keyboard = [
        [KeyboardButton(text='📊 Monthly Report'), KeyboardButton(text='📅 Yearly Report')],
        [KeyboardButton(text='💰 Total Spent')],
        [KeyboardButton(text='🔍 Last 5 Expenses'), KeyboardButton(text='❌ Delete Expense')],
        [KeyboardButton(text='📝 Manage Categories')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def create_category_management_keyboard(categories: List[Category]) -> InlineKeyboardMarkup:
    """Creates keyboard for category management with delete buttons."""
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(text=f"📁 {category.name}", callback_data=f"view_cat_{category.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"del_cat_{category.id}")
        ])

    buttons.append([InlineKeyboardButton(
        text="➕ Add New Category",
        callback_data="new_cat_manage"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def create_category_selection_keyboard(user_id: int, expense_data: str) -> InlineKeyboardMarkup:
    """
    Creates a keyboard with user's categories for expense categorization.
    The expense_data parameter contains the original expense information to be passed back.
    """
    async with get_async_session() as session:
        categories = await get_user_categories(session, user_id)

        buttons = []
        # Create buttons in rows of 2
        for i in range(0, len(categories), 2):
            row = []
            for category in categories[i:i + 2]:
                row.append(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f"cat_{category.id}_{expense_data}"
                ))
            buttons.append(row)

        # Add "Add New Category" button
        buttons.append([InlineKeyboardButton(
            text="➕ Add New Category",
            callback_data=f"new_cat_{expense_data}"
        )])

        return InlineKeyboardMarkup(inline_keyboard=buttons)


async def create_category_selection_keyboard_for_change(user_id: int, expense_id: str) -> InlineKeyboardMarkup:
    """
    Creates a keyboard with user's categories for changing expense category.
    """
    async with get_async_session() as session:
        categories = await get_user_categories(session, user_id)

        buttons = []
        # Create buttons in rows of 2
        for i in range(0, len(categories), 2):
            row = []
            for category in categories[i:i + 2]:
                row.append(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f"catchange_{category.id}_{expense_id}"
                ))
            buttons.append(row)

        return InlineKeyboardMarkup(inline_keyboard=buttons)


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