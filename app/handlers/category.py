import logging
from datetime import datetime

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.models import get_async_session
from app.db.repositories.category_repository import (
    get_user_categories,
    add_category,
    get_category_by_id,
    delete_category
)
from app.db.repositories.expense_repository import get_last_expenses, get_expense_by_id, get_expenses_by_date
from app.keyboards import create_category_management_keyboard, create_category_selection_keyboard, \
    create_category_selection_keyboard_for_change

logger = logging.getLogger(__name__)


class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_expense = State()


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
    if not callback.data.endswith('manage'):
        await state.update_data(expense_data=callback.data.split('_', 2)[2])

    await callback.message.edit_text(
        "Please enter a name for the new category:"
    )


async def process_new_category_name(message: types.Message, state: FSMContext) -> None:
    """Handles the new category name input."""
    try:
        async with get_async_session() as session:
            category = await add_category(session, message.from_user.id, message.text)
            state_data = await state.get_data()
            expense_data = state_data.get('expense_data')

            if expense_data:
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
                await message.answer(f"✅ Category '{category.name}' has been added!")
                await manage_categories(message)

            await state.clear()

    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in process_new_category_name: {e}")
        await message.answer("❌ An error occurred while creating the category")
        await state.clear()


async def delete_category_handler(callback: types.CallbackQuery) -> None:
    """Handles category deletion."""
    category_id = int(callback.data.split('_')[2])

    async with get_async_session() as session:
        categories = await get_user_categories(session, callback.from_user.id)
        if len(categories) <= 1:
            await callback.answer(
                "Cannot delete the last category. At least one category must remain.",
                show_alert=True
            )
            return

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

        try:
            result = await delete_category(
                session,
                category_id,
                callback.from_user.id,
                other_category.id
            )

            if result:
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


async def change_category_by_date(message: types.Message) -> None:
    """Handles the /change command to change expense category."""
    try:
        # Split command and get date
        _, date_str = message.text.split(maxsplit=1)
        date = datetime.strptime(date_str, '%d.%m.%y')

        async with get_async_session() as session:
            # Get expenses for the specified date
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

            # Create buttons for each expense
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
        # Get expense ID from callback data
        expense_id = int(callback.data.split('_')[1])

        async with get_async_session() as session:
            # Get the expense with its category
            expense = await get_expense_by_id(session, expense_id)

            if not expense:
                await callback.message.edit_text("❌ Expense not found")
                return

            # Prepare expense data for category selection
            expense_data = f"{expense_id}"

            # Show category selection keyboard
            keyboard = await create_category_selection_keyboard_for_change(
                callback.from_user.id,
                expense_data
            )

            # Format message with current expense details
            description_text = f" - {expense.description}" if expense.description else ""
            await callback.message.edit_text(
                f"Current category: {expense.category.name}\n"
                f"Amount: {expense.amount:.2f} UAH{description_text}\n"
                f"Date: {expense.day:02d}.{expense.month:02d}.{expense.year}\n\n"
                f"Select new category:",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in process_expense_selection_for_change: {e}")
        await callback.message.edit_text("❌ An error occurred while processing your request")


async def process_category_change(callback: types.CallbackQuery) -> None:
    """Handles category change for an expense."""
    try:
        # Parse callback data
        _, category_id, expense_id = callback.data.split('_')
        category_id = int(category_id)
        expense_id = int(expense_id)

        async with get_async_session() as session:
            # Get expense with its current category
            expense = await get_expense_by_id(session, expense_id)

            if not expense:
                await callback.message.edit_text("❌ Expense not found")
                return

            # Get new category
            new_category = await get_category_by_id(session, category_id, callback.from_user.id)
            if not new_category:
                await callback.message.edit_text("❌ Category not found")
                return

            # Save current category name before update
            old_category = expense.category.name

            # Update category
            expense.category_id = category_id
            await session.commit()

            # Format confirmation message
            description_text = f" - {expense.description}" if expense.description else ""
            await callback.message.edit_text(
                f"✅ Category changed successfully!\n\n"
                f"Amount: {expense.amount:.2f} UAH{description_text}\n"
                f"Date: {expense.day:02d}.{expense.month:02d}.{expense.year}\n"
                f"Old category: {old_category}\n"
                f"New category: {new_category.name}"
            )

    except Exception as e:
        logger.error(f"Error in process_category_change: {e}")
        await callback.message.edit_text("❌ An error occurred while changing the category")


async def change_last_expense_category(message: types.Message) -> None:
    """Handler to change category of the last recorded expense."""
    try:
        async with get_async_session() as session:
            last_expenses = await get_last_expenses(session, message.from_user.id, limit=1)

            if not last_expenses:
                await message.answer("No expenses found to change category")
                return

            last_expense = last_expenses[0]

            # Use the existing category change flow
            keyboard = await create_category_selection_keyboard_for_change(
                message.from_user.id,
                str(last_expense.id)
            )

            description_text = f" - {last_expense.description}" if last_expense.description else ""
            await message.answer(
                f"Current category: {last_expense.category.name}\n"
                f"Amount: {last_expense.amount:.2f} UAH{description_text}\n"
                f"Date: {last_expense.day:02d}.{last_expense.month:02d}.{last_expense.year}\n\n"
                "Select new category:",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in change_last_expense_category: {e}")
        await message.answer("❌ An error occurred while preparing category change")
