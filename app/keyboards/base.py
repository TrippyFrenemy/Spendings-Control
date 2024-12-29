from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Creates the main keyboard with expense tracking options."""
    keyboard = [
        [KeyboardButton(text='📈 Daily Report'), KeyboardButton(text='📊 Monthly Report')],
        [KeyboardButton(text='📅 Yearly Report')],
        [KeyboardButton(text='💰 Total Spent')],
        [KeyboardButton(text='🔍 Last 5 Expenses'), KeyboardButton(text='❌ Delete Expense')],
        [KeyboardButton(text='📝 Manage Categories')]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
