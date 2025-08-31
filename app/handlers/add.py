import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.handlers.expense import handle_expense
from app.handlers.income import handle_income

logger = logging.getLogger(__name__)


class EntryStates(StatesGroup):
    """States for adding expenses or incomes via buttons."""
    waiting_for_expense = State()
    waiting_for_income = State()


async def add_expense_button(message: types.Message, state: FSMContext) -> None:
    """Prompt user to enter expense details."""
    await state.set_state(EntryStates.waiting_for_expense)
    await message.answer(
        "Enter expense in format:\n"
        "DD.MM.YY amount description\n"
        "or amount description"
    )


async def add_income_button(message: types.Message, state: FSMContext) -> None:
    """Prompt user to enter income details."""
    await state.set_state(EntryStates.waiting_for_income)
    await message.answer(
        "Enter income in format:\n"
        "DD.MM.YY amount description\n"
        "or amount description"
    )


async def process_add_expense(message: types.Message, state: FSMContext) -> None:
    """Process expense after button prompt."""
    try:
        await handle_expense(message)
    finally:
        await state.clear()


async def process_add_income(message: types.Message, state: FSMContext) -> None:
    """Process income after button prompt."""
    try:
        await handle_income(message)
    finally:
        await state.clear()
