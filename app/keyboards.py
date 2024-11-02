from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Траты")],
    [KeyboardButton(text="Заработок")],
    [KeyboardButton(text="Отчетность")]],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню...")

spendings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="test1", callback_data="test1")],
    [InlineKeyboardButton(text="test2", callback_data="test2")],
    [InlineKeyboardButton(text="test3", callback_data="test3")]])

earns = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="test1", callback_data="test1")],
    [InlineKeyboardButton(text="test2", callback_data="test2")],
    [InlineKeyboardButton(text="test3", callback_data="test3")]])
