import logging
from datetime import datetime

from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards import (
    get_main_keyboard,
    create_year_keyboard,
    create_month_keyboard,
    create_category_selection_keyboard,
    create_category_management_keyboard,
    create_category_selection_keyboard_for_change,
)
from app.spendings import generate_monthly_report, generate_yearly_report
from app.db.requests import (
    get_or_create_user,
    get_expenses_by_date,
    add_expense,
    get_last_expenses,
    get_total_spent,
    delete_expense_by_id,
    get_user_categories,
    get_category_by_id,
    add_category,
    delete_category,
    get_expense_by_id
)
from app.db.models import get_async_session, Expense

logger = logging.getLogger(__name__)


class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_expense = State()


def register_all_handlers(dp: Dispatcher) -> None:
    # Keep existing handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(delete_by_date, Command("delete"))
    dp.message.register(change_category_by_date, Command("change"))
    dp.message.register(select_period, F.text.in_(['📊 Monthly Report']))
    dp.message.register(show_year_selection, F.text == '📅 Yearly Report')
    dp.message.register(show_delete_dates, F.text == '❌ Delete Expense')
    dp.message.register(total_spent, F.text == '💰 Total Spent')
    dp.message.register(last_expenses, F.text == '🔍 Last 5 Expenses')

    # New handlers for categories
    dp.message.register(manage_categories, F.text == '📝 Manage Categories')
    dp.callback_query.register(process_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(start_new_category, F.data.startswith("new_cat_"))
    dp.callback_query.register(delete_category_handler, F.data.startswith("del_cat_"))
    dp.message.register(process_new_category_name, CategoryStates.waiting_for_name)

    # Category change handlers
    dp.callback_query.register(process_expense_selection_for_change, F.data.startswith("change_"))
    dp.callback_query.register(process_category_change, F.data.startswith("catchange_"))

    dp.callback_query.register(process_year_selection, F.data.startswith("year_"))
    dp.callback_query.register(back_to_years, F.data == "back_to_years")
    dp.callback_query.register(process_month_selection, F.data.startswith("month_"))
    dp.callback_query.register(delete_expense, F.data.startswith("del_"))

    # Default handler for expense recording
    dp.message.register(handle_expense)


async def cmd_start(message: types.Message) -> None:
    async with get_async_session() as session:
        await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username
        )

    await message.answer(
        'Welcome to the Expense Tracker Bot!\n\n'
        'To record an expense, use the format:\n'
        'DD.MM.YY amount description\n'
        'Example: 26.12.23 500 coffee with friends\n\n'
        'You\'ll then be prompted to select a category for the expense.\n\n'
        'Use the keyboard below to access reports and manage your expenses.',
        reply_markup=get_main_keyboard()
    )


async def handle_expense(message: types.Message) -> None:
    """
    Default handler that processes expense entries.
    Now it only parses date, amount, and description, then prompts for category selection.
    """
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2:
            raise ValueError("Not enough arguments")

        # Parse date
        date = datetime.strptime(parts[0], '%d.%m.%y')
        year = 2000 + date.year % 100

        # Parse amount
        amount = float(parts[1])

        # Get description (optional)
        description = parts[2] if len(parts) > 2 else None

        # Create temporary data string for callback
        expense_data = f"{date.day},{date.month},{year},{amount}"
        if description:
            expense_data += f",{description}"

        # Show category selection keyboard
        keyboard = await create_category_selection_keyboard(message.from_user.id, expense_data)
        await message.answer(
            "Please select a category for your expense:",
            reply_markup=keyboard
        )

    except ValueError as e:
        logger.error(f"Value error in handle_expense: {e}")
        await message.answer(
            "❌ Invalid format. Please use: DD.MM.YY amount description\n"
            "Example: 26.12.23 500 coffee with friends"
        )
    except Exception as e:
        logger.error(f"Unexpected error in handle_expense: {e}")
        await message.answer("❌ An error occurred while recording the expense")


async def process_category_selection(callback: types.CallbackQuery) -> None:
    """Handles category selection for an expense."""
    try:
        # Parse callback data
        _, category_id, *expense_data = callback.data.split('_')
        category_id = int(category_id)
        expense_data = expense_data[0].split(',')

        # Parse expense data
        day = int(expense_data[0])
        month = int(expense_data[1])
        year = int(expense_data[2])
        amount = float(expense_data[3])
        description = expense_data[4] if len(expense_data) > 4 else None

        async with get_async_session() as session:
            # Add expense with selected category
            expense = await add_expense(
                session,
                callback.from_user.id,
                day,
                month,
                year,
                amount,
                category_id,
                description
            )

            # Get category name for confirmation message
            categories = await get_user_categories(session, callback.from_user.id)
            category_name = next(cat.name for cat in categories if cat.id == category_id)

            # Format confirmation message
            message = f"✅ Recorded: {amount:.2f} UAH"
            if description:
                message += f" for {description}"
            message += f"\nCategory: {category_name}\nDate: {day:02d}.{month:02d}.{year}"

            await callback.message.edit_text(message)

    except Exception as e:
        logger.error(f"Error in process_category_selection: {e}")
        await callback.message.edit_text("❌ An error occurred while categorizing the expense")


async def manage_categories(message: types.Message) -> None:
    """Shows the list of user's categories with options to add/edit/delete."""
    async with get_async_session() as session:
        categories = await get_user_categories(session, message.from_user.id)

        if not categories:
            await message.answer(
                "You don't have any categories yet. Add your first category:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="➕ Add New Category",
                        callback_data="new_cat_manage"
                    )
                ]])
            )
            return

        keyboard = await create_category_management_keyboard(categories)
        await message.answer(
            "Manage your expense categories:\n"
            "Click on ❌ to delete a category",
            reply_markup=keyboard
        )


async def start_new_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Initiates the process of adding a new category."""
    await state.set_state(CategoryStates.waiting_for_name)
    # Store the original expense data if we're in the middle of expense creation
    if not callback.data.endswith('manage'):
        await state.update_data(expense_data=callback.data.split('_', 2)[2])

    await callback.message.edit_text(
        "Please enter a name for the new category:"
    )


async def process_new_category_name(message: types.Message, state: FSMContext) -> None:
    """Handles the new category name input."""
    try:
        async with get_async_session() as session:
            # Create new category
            category = await add_category(session, message.from_user.id, message.text)

            # Check if we're in the middle of expense creation
            state_data = await state.get_data()
            expense_data = state_data.get('expense_data')

            if expense_data:
                # If we were creating an expense, show category selection again
                keyboard = await create_category_selection_keyboard(
                    message.from_user.id,
                    expense_data
                )
                await message.answer(
                    f"Category '{category.name}' created!\n"
                    f"Now please select a category for your expense:",
                    reply_markup=keyboard
                )
            else:
                # If we were just managing categories, show updated list
                await message.answer(f"✅ Category '{category.name}' has been added!")
                await manage_categories(message)

            await state.clear()

    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in process_new_category_name: {e}")
        await message.answer("❌ An error occurred while creating the category")
        await state.clear()


async def change_category_by_date(message: types.Message) -> None:
    """Handles the /change command to change expense category."""
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
                button_text = (
                    f"{expense.amount:.2f} UAH - {expense.category.name}"
                    f"{f' ({expense.description})' if expense.description else ''}"
                )
                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"change_{expense.id}"
                    )
                ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(
                f"Select an expense to change category for {date_str}:",
                reply_markup=keyboard
            )

    except ValueError:
        await message.answer(
            "❌ Incorrect date format. Please use: /change DD.MM.YY\n"
            "Example: /change 26.12.23"
        )
    except Exception as e:
        logger.error(f"Error in change_category_by_date: {e}")
        await message.answer("❌ An error occurred while processing your request")


async def process_expense_selection_for_change(callback: types.CallbackQuery) -> None:
    """Handles expense selection for category change."""
    try:
        expense_id = int(callback.data.split('_')[1])

        async with get_async_session() as session:
            # Get the expense with its category
            expense = await get_expense_by_id(session, expense_id)

            if not expense:
                await callback.message.edit_text("❌ Expense not found")
                return

            # Format expense data for category selection
            expense_data = f"{expense_id}"

            # Show category selection keyboard
            keyboard = await create_category_selection_keyboard_for_change(
                callback.from_user.id,
                expense_data
            )

            description_text = f" - {expense.description}" if expense.description else ""
            await callback.message.edit_text(
                f"Current category: {expense.category.name}\n"
                f"Amount: {expense.amount:.2f} UAH{description_text}\n\n"
                f"Select new category:",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in process_expense_selection_for_change: {e}")
        await callback.message.edit_text("❌ An error occurred while processing your request")


async def process_category_change(callback: types.CallbackQuery) -> None:
    """Handles category change for an expense."""
    try:
        _, category_id, expense_id = callback.data.split('_')
        category_id = int(category_id)
        expense_id = int(expense_id)

        async with get_async_session() as session:
            # Get expense with its category
            expense = await get_expense_by_id(session, expense_id)

            if not expense:
                await callback.message.edit_text("❌ Expense not found")
                return

            category = await get_category_by_id(session, category_id, callback.from_user.id)
            if not category:
                await callback.message.edit_text("❌ Category not found")
                return

            # Update category
            old_category = expense.category.name
            expense.category_id = category_id
            await session.commit()

            description_text = f" - {expense.description}" if expense.description else ""
            await callback.message.edit_text(
                f"✅ Category changed successfully!\n\n"
                f"Amount: {expense.amount:.2f} UAH{description_text}\n"
                f"Old category: {old_category}\n"
                f"New category: {category.name}"
            )

    except Exception as e:
        logger.error(f"Error in process_category_change: {e}")
        await callback.message.edit_text("❌ An error occurred while changing the category")


async def delete_category_handler(callback: types.CallbackQuery) -> None:
    """Handles category deletion."""
    category_id = int(callback.data.split('_')[2])

    async with get_async_session() as session:
        # Check if this is the last category
        categories = await get_user_categories(session, callback.from_user.id)
        if len(categories) <= 1:
            await callback.answer(
                "Cannot delete the last category. At least one category must remain.",
                show_alert=True
            )
            return

        # Get 'Other' category or first available category for moving expenses
        other_category = next(
            (cat for cat in categories if cat.name == "Other" and cat.id != category_id),
            next((cat for cat in categories if cat.id != category_id), None)
        )

        if not other_category:
            await callback.answer(
                "Error: No alternative category available",
                show_alert=True
            )
            return

        # Delete category and move expenses
        try:
            result = await delete_category(
                session,
                category_id,
                callback.from_user.id,
                other_category.id
            )

            if result:
                # Update the category management keyboard
                updated_categories = await get_user_categories(session, callback.from_user.id)
                keyboard = await create_category_management_keyboard(updated_categories)

                await callback.message.edit_text(
                    "Manage your expense categories:\n"
                    "Click on ❌ to delete a category",
                    reply_markup=keyboard
                )
                await callback.answer(
                    f"Category deleted. Expenses moved to {other_category.name}",
                    show_alert=True
                )
            else:
                await callback.answer(
                    "Error deleting category",
                    show_alert=True
                )
        except Exception as e:
            logger.error(f"Error in delete_category_handler: {e}")
            await callback.answer(
                "Error occurred while deleting category",
                show_alert=True
            )


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
    """Shows last 5 recorded expenses with their categories."""
    async with get_async_session() as session:
        expenses = await get_last_expenses(session, message.from_user.id)
        if not expenses:
            await message.answer("No expenses recorded yet")
            return

        text = "Last 5 expenses:\n\n"
        for expense in expenses:
            text += (
                f"📅 {expense.day:02d}.{expense.month:02d}.{expense.year}\n"
                f"💵 {expense.amount:.2f} UAH - {expense.category.name}\n"
            )
            if expense.description:
                text += f"📝 {expense.description}\n"
            text += "\n"
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