from aiogram import Dispatcher, F
from aiogram.filters import Command

from app.handlers.base import cmd_start
from app.handlers.category import (
    manage_categories, start_new_category, delete_category_handler,
    process_new_category_name, CategoryStates, change_category_by_date, process_expense_selection_for_change, \
    process_category_change
)
from app.handlers.deletion import (
    delete_by_date,
    show_delete_dates,
    delete_expense,
    show_delete_income_dates,
    delete_income,
    delete_income_by_date,
)
from app.handlers.expense import handle_expense, process_category_selection
from app.handlers.reports import (
    select_period, show_year_selection, total_spent, last_expenses, process_year_selection,
    process_month_selection, back_to_years, process_daily_month_selection, select_daily_breakdown
)
from app.handlers.income import handle_income, total_income, last_incomes, balance
from app.handlers.add import add_expense_button, add_income_button, process_add_expense, process_add_income, EntryStates
from app.handlers.graphs import graph_daily, graph_monthly


def register_all_handlers(dp: Dispatcher) -> None:
    # Start command handler
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(delete_by_date, Command("delete"))
    dp.message.register(delete_income_by_date, Command("delete_income"))
    dp.message.register(change_category_by_date, Command("change"))

    # Add entry handlers
    dp.message.register(add_expense_button, F.text == '➕ Add Expense')
    dp.message.register(add_income_button, F.text == '➕ Add Income')
    dp.message.register(process_add_expense, EntryStates.waiting_for_expense)
    dp.message.register(process_add_income, EntryStates.waiting_for_income)

    # Report handlers
    dp.message.register(select_daily_breakdown, F.text == '📈 Daily Report')
    dp.message.register(select_period, F.text.in_(['📊 Monthly Report']))
    dp.message.register(show_year_selection, F.text == '📅 Yearly Report')

    # Deletion handlers
    dp.message.register(show_delete_dates, F.text == '❌ Delete Expense')
    dp.message.register(show_delete_income_dates, F.text == '❌ Delete Income')

    # Expense handlers
    dp.message.register(total_spent, F.text == '💰 Total Spent')
    dp.message.register(last_expenses, F.text == '🔍 Last 5 Expenses')
    dp.message.register(last_expenses, Command("expenses"))

    # Income handlers
    dp.message.register(total_income, F.text == '💵 Total Income')
    dp.message.register(last_incomes, F.text == '🔍 Last 5 Incomes')
    dp.message.register(balance, F.text == '📊 Balance')

    # Graph handlers
    dp.message.register(graph_daily, Command("graph_day"))
    dp.message.register(graph_monthly, Command("graph_month"))

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
    dp.callback_query.register(delete_income, F.data.startswith("deli_"))

    dp.callback_query.register(process_daily_month_selection, F.data.startswith("daily_month_"))  # New handler
    dp.message.register(handle_income, Command("income"))

    # Default handler for expense recording
    dp.message.register(handle_expense, lambda m: m.text not in ['➕ Add Expense', '➕ Add Income'])
    