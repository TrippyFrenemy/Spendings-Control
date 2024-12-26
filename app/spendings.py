import io
import logging
from datetime import datetime
import calendar
import pandas as pd
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile, Message
from typing import Tuple, List

from app.db.models import get_async_session
from app.db.requests import get_yearly_expenses, get_monthly_expenses

logger = logging.getLogger(__name__)


async def generate_yearly_report(message: Message, year: int) -> None:
    """
    Generates and sends a yearly expense report with visualizations.

    Args:
        message: The message object for sending responses
        year: The year to generate the report for
    """
    user_id = message.chat.id
    logging.info(f"Generating yearly report for user {user_id}, year {year}")

    async with get_async_session() as session:
        yearly_data = await get_yearly_expenses(session, user_id, year)
        logging.info(f"Received yearly data: {yearly_data}")

        if not yearly_data:
            await message.answer(f"No expenses found for {year}")
            return

        # Process data for visualization
        df = pd.DataFrame(yearly_data, columns=['month', 'category', 'amount'])

        # Create stacked bar chart
        plt.figure(figsize=(12, 6))
        pivot_table = df.pivot_table(
            index='month',
            columns='category',
            values='amount',
            fill_value=0
        )

        # Generate visualization
        pivot_table.plot(kind='bar', stacked=True)
        plt.title(f'Yearly Expenses {year}')
        plt.xlabel('Month')
        plt.ylabel('Amount (UAH)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        # Generate summary text
        total = df['amount'].sum()
        category_total = df.groupby('category')['amount'].sum()
        summary = f"Year {year}:\nTotal: {total:.2f} UAH\n\nBy category:\n"
        for cat, amount in category_total.items():
            percentage = (amount / total) * 100
            summary += f"{cat}: {amount:.2f} UAH ({percentage:.1f}%)\n"

        # Send report
        await message.answer_photo(
            BufferedInputFile(buf.getvalue(), filename="yearly_report.png"),
            caption=summary
        )


async def generate_monthly_report(message: Message, year: int, month: int) -> None:
    """
    Generates and sends a monthly expense report with visualizations.

    Args:
        message: The message object for sending responses
        year: The year to generate the report for
        month: The month to generate the report for
    """
    async with get_async_session() as session:
        monthly_data = await get_monthly_expenses(session, message.chat.id, year, month)

        if not monthly_data:
            await message.answer(f"No expenses for {calendar.month_name[month]} {year}")
            return

        # Prepare data for visualization
        categories, amounts = zip(*[(cat, amount) for cat, amount in monthly_data])

        # Create bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(categories, amounts)
        plt.title(f'Monthly Expenses ({calendar.month_name[month]} {year})')
        plt.ylabel('Amount (UAH)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        # Calculate total and prepare summary
        total = sum(amounts)

        # Generate detailed summary with percentages
        category_details = []
        for cat, amount in zip(categories, amounts):
            percentage = (amount / total) * 100
            category_details.append(f"{cat}: {amount:.2f} UAH ({percentage:.1f}%)")

        summary = (
                f"Total for {calendar.month_name[month]} {year}: {total:.2f} UAH\n\n"
                "Breakdown by category:\n" + "\n".join(category_details)
        )

        # Send report
        await message.answer_photo(
            BufferedInputFile(buf.getvalue(), filename="monthly_report.png"),
            caption=summary
        )


def format_expense_amount(amount: float) -> str:
    """
    Formats expense amount with proper decimal places and currency.

    Args:
        amount: The amount to format
    Returns:
        Formatted string with amount and currency
    """
    return f"{amount:.2f} UAH"