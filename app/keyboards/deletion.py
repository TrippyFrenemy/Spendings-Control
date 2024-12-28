from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_delete_confirmation_keyboard(expense_id: int) -> InlineKeyboardMarkup:
    """Creates a confirmation keyboard for expense deletion."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"del_{expense_id}_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"del_{expense_id}_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
