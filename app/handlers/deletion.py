# app/handlers/deletion.py
import logging
from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.models import get_async_session
from app.db.repositories.expense_repository import (
    get_expenses_by_date, delete_expense_by_id,
    get_expense_by_id, get_last_expenses
)

logger = logging.getLogger(__name__)


async def show_delete_dates(message: types.Message) -> None:
    """Shows expenses that can be deleted."""
    async with get_async_session() as session:
        today = datetime.now()
        expenses = await get_expenses_by_date(
            session,
            message.from_user.id,
            today.day,
            today.month,
            today.year
        )

        if not expenses:
            await message.answer(
                "No expenses found for today.\n"
                "To delete expenses from another date, use:\n"
                "/delete DD.MM.YY"
            )
            return

        buttons = []
        for expense in expenses:
            button_text = (
                f"{expense.amount:.2f} UAH - {expense.description} "
                f"({expense.day:02d}.{expense.month:02d}.{expense.year})"
            )
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"del_{expense.id}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "Select an expense to delete:\n"
            "⚠️ This action cannot be undone",
            reply_markup=keyboard
        )


async def delete_expense(callback: types.CallbackQuery) -> None:
    """Processes expense deletion."""
    try:
        expense_id = int(callback.data.split('_')[1])

        async with get_async_session() as session:
            if await delete_expense_by_id(session, expense_id, callback.from_user.id):
                await callback.message.edit_text("✅ Expense deleted successfully")

                # Show remaining expenses
                today = datetime.now()
                remaining_expenses = await get_expenses_by_date(
                    session,
                    callback.from_user.id,
                    today.day,
                    today.month,
                    today.year
                )

                if remaining_expenses:
                    buttons = []
                    for expense in remaining_expenses:
                        button_text = (
                            f"{expense.amount:.2f} UAH - {expense.description} "
                            f"({expense.day:02d}.{expense.month:02d}.{expense.year})"
                        )
                        buttons.append([
                            InlineKeyboardButton(
                                text=button_text,
                                callback_data=f"del_{expense.id}"
                            )
                        ])
                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                    await callback.message.answer(
                        "Remaining expenses:",
                        reply_markup=keyboard
                    )
            else:
                await callback.message.edit_text(
                    "❌ Could not delete expense: not found"
                )

    except Exception as e:
        logger.error(f"Error during expense deletion: {e}")
        await callback.message.edit_text(
            "❌ An error occurred while deleting the expense"
        )


async def delete_by_date(message: types.Message) -> None:
    """Handles deletion of expenses from specific dates."""
    try:
        _, date_str = message.text.split(maxsplit=1)
        date = datetime.strptime(date_str, '%d.%m.%y')

        async with get_async_session() as session:
            expenses = await get_expenses_by_date(
                session,
                message.from_user.id,
                date.day,
                date.month,
                2000 + date.year % 100
            )

            if not expenses:
                await message.answer(f"No expenses found for {date_str}")
                return

            buttons = []
            for expense in expenses:
                button_text = f"{expense.amount:.2f} UAH - {expense.description}"
                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"del_{expense.id}"
                    )
                ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(
                f"Select an expense to delete for {date_str}:",
                reply_markup=keyboard
            )

    except ValueError:
        await message.answer(
            "❌ Incorrect date format. Please use: /delete DD.MM.YY\n"
            "Example: /delete 26.12.23"
        )
    except Exception as e:
        logger.error(f"Error in delete_by_date: {e}")
        await message.answer("❌ An error occurred while processing your request")
