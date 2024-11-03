from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.requests import get_categories

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Траты")],
    [KeyboardButton(text="Заработок")],
    [KeyboardButton(text="Отчетность")]],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню...")

# spendings = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text="test1", callback_data="test1")],
#     [InlineKeyboardButton(text="test2", callback_data="test2")],
#     [InlineKeyboardButton(text="test3", callback_data="test3")]])
#
# earns = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text="test1", callback_data="test1")],
#     [InlineKeyboardButton(text="test2", callback_data="test2")],
#     [InlineKeyboardButton(text="test3", callback_data="test3")]])


async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))

    keyboard.add(InlineKeyboardButton(text="На главную", callback_data="to_main"))
    return keyboard.adjust(2).as_markup()
