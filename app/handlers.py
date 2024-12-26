import logging
from datetime import datetime
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards import (
    get_main_keyboard,
    create_year_keyboard,
    create_month_keyboard,
)
from app.spendings import generate_monthly_report, generate_yearly_report
from app.db.requests import (
    get_or_create_user,
    get_expenses_by_date,
    add_expense,
    get_last_expenses,
    get_total_spent,
    delete_expense_by_id
)
from app.db.models import get_async_session

logger = logging.getLogger(__name__)


def register_all_handlers(dp: Dispatcher) -> None:
    """
    Registers all message and callback handlers with the dispatcher.
    This function organizes all the bot's commands and interactions.
    """
    # Command handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(delete_by_date, Command("delete"))

    # Main menu handlers
    dp.message.register(select_period, F.text.in_(['📊 Monthly Report']))
    dp.message.register(show_year_selection, F.text == '📅 Yearly Report')
    dp.message.register(show_delete_dates, F.text == '❌ Delete Expense')
    dp.message.register(total_spent, F.text == '💰 Total Spent')
    dp.message.register(last_expenses, F.text == '🔍 Last 5 Expenses')

    # Callback query handlers
    dp.callback_query.register(process_year_selection, F.data.startswith("year_"))
    dp.callback_query.register(back_to_years, F.data == "back_to_years")
    dp.callback_query.register(process_month_selection, F.data.startswith("month_"))
    dp.callback_query.register(delete_expense, F.data.startswith("del_"))

    # Default handler for expense recording
    dp.message.register(handle_expense)


async def cmd_start(message: types.Message) -> None:
    """
    Handles the /start command. Creates a new user if they don't exist
    and shows the welcome message with the main keyboard.
    """
    async with get_async_session() as session:
        await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username
        )

    await message.answer(
        'Welcome to the Expense Tracker Bot!\n\n'
        'To record an expense, use the format:\n'
        'DD.MM.YY amount category\n'
        'Example: 26.12.23 500 coffee\n\n'
        'Use the keyboard below to access reports and manage your expenses.',
        reply_markup=get_main_keyboard()
    )


async def handle_expense(message: types.Message) -> None:
    """
    Default handler that processes expense entries.
    Parses the message and saves the expense to the database.
    """
    try:
        text = message.text.split()
        if len(text) < 3:
            raise ValueError("Not enough arguments")

        # Parse date and convert two-digit year to full year
        date = datetime.strptime(text[0], '%d.%m.%y')
        year = 2000 + date.year % 100

        # Parse amount and category
        amount = float(text[1])
        category = text[2].lower()

        logger.info(
            f"Adding expense: date={date}, amount={amount}, "
            f"category={category}, user={message.from_user.id}"
        )

        async with get_async_session() as session:
            expense = await add_expense(
                session,
                message.from_user.id,
                date.day,
                date.month,
                year,
                amount,
                category
            )
            logger.info(f"Expense added successfully: {expense.id}")
            await message.answer(
                f"✅ Recorded: {amount:.2f} UAH for {category} "
                f"on {date.strftime('%d.%m.%y')}"
            )

    except ValueError as e:
        logger.error(f"Value error in handle_expense: {e}")
        await message.answer(
            "❌ Invalid format. Please use: DD.MM.YY amount category\n"
            "Example: 26.12.23 500 coffee"
        )
    except Exception as e:
        logger.error(f"Unexpected error in handle_expense: {e}")
        await message.answer("❌ An error occurred while recording the expense")


async def select_period(message: types.Message) -> None:
    """Handles the selection of year for monthly reports."""
    keyboard = await create_year_keyboard(message.from_user.id)
    await message.answer(
        f"Select year for {message.text}:",
        reply_markup=keyboard
    )


async def process_year_selection(callback: types.CallbackQuery) -> None:
    """
    Processes year selection from inline keyboard.
    Redirects to either yearly report generation or month selection.
    """
    year = int(callback.data.split('_')[1])
    report_type = "yearly" if "yearly report" in callback.message.text.lower() else "monthly"

    if report_type == "yearly":
        await generate_yearly_report(callback.message, year)
    else:
        await callback.message.edit_text(
            f"Selected year: {year}\nSelect month:",
            reply_markup=create_month_keyboard(year)
        )


async def process_month_selection(callback: types.CallbackQuery) -> None:
    """Processes month selection and generates appropriate report."""
    _, year, month = callback.data.split('_')
    year = int(year)
    month = int(month)

    async with get_async_session() as session:
        await generate_monthly_report(callback.message, year, month)

    await callback.message.delete()


async def back_to_years(callback: types.CallbackQuery) -> None:
    """Returns to year selection keyboard."""
    await callback.message.edit_text(
        "Select year:",
        reply_markup=await create_year_keyboard(callback.from_user.id)
    )


async def show_year_selection(message: types.Message) -> None:
    """Shows year selection for yearly reports."""
    await message.answer(
        "Select year for yearly report:",
        reply_markup=await create_year_keyboard(message.from_user.id)
    )


async def total_spent(message: types.Message) -> None:
    """Shows total amount spent across all time."""
    async with get_async_session() as session:
        total = await get_total_spent(session, message.from_user.id)
        await message.answer(
            f"💰 Total spent: {total:.2f} UAH\n"
            f"Keep track of your expenses!"
        )


async def last_expenses(message: types.Message) -> None:
    """Shows last 5 recorded expenses."""
    async with get_async_session() as session:
        expenses = await get_last_expenses(session, message.from_user.id)
        if not expenses:
            await message.answer("No expenses recorded yet")
            return

        text = "Last 5 expenses:\n\n"
        for expense in expenses:
            text += (
                f"📅 {expense.day:02d}.{expense.month:02d}.{expense.year}\n"
                f"💵 {expense.amount:.2f} UAH - {expense.category}\n\n"
            )
        await message.answer(text)


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
                f"{expense.amount:.2f} UAH - {expense.category} "
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
                            f"{expense.amount:.2f} UAH - {expense.category} "
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
                button_text = f"{expense.amount:.2f} UAH - {expense.category}"
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