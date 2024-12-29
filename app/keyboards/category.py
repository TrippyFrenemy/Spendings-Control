from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.db.models import get_async_session
from app.db.repositories.category_repository import get_user_categories


async def create_category_management_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Creates keyboard for category management with delete buttons."""
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(text=f"📁 {category['name']}", callback_data=f"view_cat_{category['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"del_cat_{category['id']}")
        ])

    buttons.append([InlineKeyboardButton(
        text="➕ Add New Category",
        callback_data="new_cat_manage"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def create_category_selection_keyboard(user_id: int, expense_data: str) -> InlineKeyboardMarkup:
    """Creates a keyboard with user's categories for expense categorization."""
    async with get_async_session() as session:
        categories = await get_user_categories(session, user_id)

        buttons = []
        for i in range(0, len(categories), 2):
            row = []
            for category in categories[i:i + 2]:
                row.append(InlineKeyboardButton(
                    text=category['name'],
                    callback_data=f"cat_{category['id']}_{expense_data}"
                ))
            buttons.append(row)

        buttons.append([InlineKeyboardButton(
            text="➕ Add New Category",
            callback_data=f"new_cat_{expense_data}"
        )])

        return InlineKeyboardMarkup(inline_keyboard=buttons)


async def create_category_selection_keyboard_for_change(user_id: int, expense_id: str) -> InlineKeyboardMarkup:
    """Creates a keyboard with user's categories for changing expense category."""
    async with get_async_session() as session:
        categories = await get_user_categories(session, user_id)

        buttons = []
        for i in range(0, len(categories), 2):
            row = []
            for category in categories[i:i + 2]:
                row.append(InlineKeyboardButton(
                    text=category['name'],
                    callback_data=f"catchange_{category['id']}_{expense_id}"
                ))
            buttons.append(row)

        return InlineKeyboardMarkup(inline_keyboard=buttons)
