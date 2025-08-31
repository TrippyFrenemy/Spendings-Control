import logging
from datetime import datetime

from aiogram import types

from app.spendings import (
    generate_income_expense_daily_graph,
    generate_income_expense_monthly_graph,
)

logger = logging.getLogger(__name__)


async def graph_daily(message: types.Message) -> None:
    """Handle /graph_day command."""
    try:
        parts = message.text.split()
        if len(parts) > 1:
            date = datetime.strptime(parts[1], "%m.%Y")
            month, year = date.month, date.year
        else:
            now = datetime.now()
            month, year = now.month, now.year
        await generate_income_expense_daily_graph(message, year, month)
    except ValueError:
        await message.answer("❌ Incorrect format. Use: /graph_day MM.YYYY")
    except Exception as e:
        logger.error(f"Error in graph_daily: {e}")
        await message.answer("❌ Could not generate graph")


async def graph_monthly(message: types.Message) -> None:
    """Handle /graph_month command."""
    try:
        parts = message.text.split()
        if len(parts) > 1:
            year = int(parts[1])
        else:
            year = datetime.now().year
        await generate_income_expense_monthly_graph(message, year)
    except ValueError:
        await message.answer("❌ Incorrect format. Use: /graph_month YYYY")
    except Exception as e:
        logger.error(f"Error in graph_monthly: {e}")
        await message.answer("❌ Could not generate graph")
        