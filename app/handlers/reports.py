import logging
from aiogram import types
from app.db.models import get_async_session
from app.db.repositories.user_repository import get_total_spent
from app.db.repositories.expense_repository import get_last_expenses
from app.keyboards import create_year_keyboard, create_month_keyboard
from app.spendings import generate_monthly_report, generate_yearly_report, generate_daily_report

logger = logging.getLogger(__name__)


async def select_daily_breakdown(message: types.Message) -> None:
    """Handles the selection of year for daily breakdown."""
    keyboard = await create_year_keyboard(message.from_user.id, "daily")
    await message.answer(
        "Select year for Daily Breakdown:",
        reply_markup=keyboard
    )


async def select_period(message: types.Message) -> None:
    """Handles the selection of year for monthly reports."""
    keyboard = await create_year_keyboard(message.from_user.id, "monthly")
    await message.answer(
        f"Select year for {message.text}:",
        reply_markup=keyboard
    )


async def process_year_selection(callback: types.CallbackQuery) -> None:
    """Processes year selection and redirects to appropriate report."""
    year = int(callback.data.split('_')[1])
    report_type = callback.data.split('_')[2] if len(callback.data.split('_')) > 2 else "monthly"

    if "yearly report" in callback.message.text.lower():
        await generate_yearly_report(callback.message, year)
    else:
        await callback.message.edit_text(
            f"Selected year: {year}\nSelect month:",
            reply_markup=create_month_keyboard(year, report_type)
        )


async def process_month_selection(callback: types.CallbackQuery) -> None:
    """Processes month selection and shows monthly report."""
    _, year, month = callback.data.split('_')
    year, month = int(year), int(month)
    await generate_monthly_report(callback.message, year, month)


async def process_daily_month_selection(callback: types.CallbackQuery) -> None:
    """Processes month selection for daily breakdown."""
    _, _, year, month = callback.data.split('_')
    year, month = int(year), int(month)
    await generate_daily_report(callback.message, year, month)


async def show_year_selection(message: types.Message) -> None:
    """Shows year selection for yearly reports."""
    await message.answer(
        "Select year for yearly report:",
        reply_markup=await create_year_keyboard(message.from_user.id, "yearly")
    )


async def back_to_years(callback: types.CallbackQuery) -> None:
    """Returns to year selection keyboard."""
    report_type = "daily" if "Daily Breakdown" in callback.message.text else "monthly"
    await callback.message.edit_text(
        "Select year:",
        reply_markup=await create_year_keyboard(callback.from_user.id, report_type)
    )


# Rest of the code remains the same
async def total_spent(message: types.Message) -> None:
    """Shows total amount spent across all time."""
    async with get_async_session() as session:
        total = await get_total_spent(session, message.from_user.id)
        await message.answer(
            f"💰 Total spent: {total:.2f} UAH\n"
            f"Keep track of your expenses!"
        )


async def last_expenses(message: types.Message) -> None:
    """Shows last 5 recorded expenses with their categories."""
    async with get_async_session() as session:
        expenses = await get_last_expenses(session, message.from_user.id)
        if not expenses:
            await message.answer("No expenses recorded yet")
            return

        text = "Last 5 expenses:\n\n"
        for expense in expenses:
            text += (
                f"📅 {expense['day']:02d}.{expense['month']:02d}.{expense['year']}\n"
                f"💵 {expense['amount']:.2f} UAH - {expense['category']['name']}\n"
            )
            if expense['description']:
                text += f"📝 {expense['description']}\n"
            text += "\n"
        await message.answer(text)
