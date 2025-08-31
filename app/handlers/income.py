import logging
from datetime import datetime

from aiogram import types

from app.handlers.expense import parse_date_from_text, parse_amount_and_description
from app.db.models import get_async_session
from app.db.repositories.income_repository import (
    add_income,
    get_total_income,
    get_last_incomes,
)
from app.db.repositories.user_repository import get_total_spent

logger = logging.getLogger(__name__)


async def handle_income(message: types.Message) -> None:
    """Handles /income command to record incomes."""
    try:
        text = message.text
        if text.startswith('/income'):
            text = text[len('/income'):].strip()
        parts = text.split(maxsplit=2)
        if len(parts) < 1 or parts[0] == '':
            raise ValueError("Not enough arguments")

        date, has_date = parse_date_from_text(parts)
        amount, description = parse_amount_and_description(parts, has_date)

        async with get_async_session() as session:
            await add_income(
                session,
                message.from_user.id,
                date.day,
                date.month,
                date.year,
                amount,
                description,
            )

        response = (
            f"✅ Income recorded: {amount:.2f} UAH\n"
            f"Date: {date.day:02d}.{date.month:02d}.{date.year}"
        )
        if description:
            response += f"\nDescription: {description}"
        await message.answer(response)
    except ValueError:
        await message.answer(
            "❌ Invalid format. Please use either:\n"
            "/income DD.MM.YY amount description\n"
            "/income amount description"
        )
    except Exception as e:
        logger.error(f"Unexpected error in handle_income: {e}")
        await message.answer("❌ An error occurred while recording the income")


async def total_income(message: types.Message) -> None:
    """Shows total income across all time."""
    async with get_async_session() as session:
        total = await get_total_income(session, message.from_user.id)
    await message.answer(f"💵 Total income: {total:.2f} UAH")


async def last_incomes(message: types.Message) -> None:
    """Shows last recorded incomes."""
    async with get_async_session() as session:
        incomes = await get_last_incomes(session, message.from_user.id)

    if not incomes:
        await message.answer("No incomes recorded yet")
        return

    text = "Last incomes:\n\n"
    for inc in incomes:
        text += (
            f"📅 {inc['day']:02d}.{inc['month']:02d}.{inc['year']}\n"
            f"💰 {inc['amount']:.2f} UAH\n"
        )
        if inc['description']:
            text += f"📝 {inc['description']}\n"
        text += "\n"
    await message.answer(text)


async def balance(message: types.Message) -> None:
    """Shows balance between incomes and expenses."""
    async with get_async_session() as session:
        income = await get_total_income(session, message.from_user.id)
        spent = await get_total_spent(session, message.from_user.id)
    diff = income - spent
    await message.answer(
        f"📊 Balance:\n"
        f"Income: {income:.2f} UAH\n"
        f"Expenses: {spent:.2f} UAH\n"
        f"Net: {diff:.2f} UAH"
    )
    