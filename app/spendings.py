import io
import logging
import calendar
import pandas as pd
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile, Message

from app.db.models import get_async_session
from app.db.redis.redis_client import redis
from app.db.repositories.expense_repository import get_yearly_expenses, get_monthly_expenses, get_daily_expenses

logger = logging.getLogger(__name__)


async def generate_yearly_report(message: Message, year: int) -> None:
    """
    Generates and sends a yearly expense report with visualizations.
    """
    user_id = message.chat.id
    logging.info(f"Generating yearly report for user {user_id}, year {year}")

    async with get_async_session() as session:
        yearly_data = await get_yearly_expenses(session, user_id, year)

        if not yearly_data:
            await message.answer(f"No expenses found for {year}")
            return

        # Check if we have cached image
        image_key = f"report_image:yearly:{user_id}:{year}"
        cached_image = await redis.get(image_key)

        if cached_image:
            await message.answer_photo(
                BufferedInputFile(cached_image, filename=f"yearly_report_{message.chat.id}.png"),
                caption=await generate_yearly_summary(yearly_data, year)
            )
            return

        # Process data for visualization
        df = pd.DataFrame([{
            'month': item['month'],
            'category': item['category'],
            'total': item['total']
        } for item in yearly_data])

        # Create a complete DataFrame with all months
        all_months = pd.DataFrame({'month': range(1, 13)})

        # Merge with actual data
        complete_df = all_months.merge(df, on='month', how='left')
        complete_df['total'] = complete_df['total'].fillna(0)
        complete_df['category'] = complete_df['category'].fillna('')

        # Create pivot table
        pivot_table = complete_df.pivot_table(
            index='month',
            columns='category',
            values='total',
            fill_value=0
        )

        # Create figure and generate visualization
        plt.figure(figsize=(20, 10))
        ax = pivot_table.plot(kind='bar', stacked=True, width=0.8, figsize=(20, 10))

        # Customize appearance
        plt.title(f'Yearly Expenses - {year}', pad=20, fontsize=14)
        plt.xlabel('Month', fontsize=12, labelpad=10)
        plt.ylabel('Amount (UAH)', fontsize=12, labelpad=10)

        # Set x-axis ticks and labels using month names
        month_names = [calendar.month_abbr[m] for m in range(1, 13)]
        plt.xticks(range(12), month_names, rotation=45, ha='right')

        # Add sum labels on top of bars
        monthly_sums = pivot_table.sum(axis=1)
        for i, sum_value in enumerate(monthly_sums):
            if sum_value > 0:  # Only show label if there are expenses
                plt.text(i, sum_value, f'{sum_value:,.0f}',
                         ha='center', va='bottom')

        # Adjust legend and add grid
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Ensure proper spacing
        plt.subplots_adjust(bottom=0.15, right=0.85)
        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        image_data = buf.getvalue()
        plt.close()

        # Cache the image
        await redis.set(image_key, image_data, ex=900)  # 15 minutes cache

        # Generate summary and send report
        summary = await generate_yearly_summary(yearly_data, year)
        await message.answer_photo(
            BufferedInputFile(image_data, filename=f"yearly_report_{message.chat.id}.png"),
            caption=summary
        )


async def generate_yearly_summary(yearly_data: list, year: int) -> str:
    """Generate summary text for yearly report."""
    df = pd.DataFrame(yearly_data)
    total = df['total'].sum()
    category_total = df.groupby('category')['total'].sum()

    summary = f"Year {year}:\nTotal: {total:.2f} UAH\n\nBy category:\n"
    for cat, amount in category_total.items():
        percentage = (amount / total) * 100
        summary += f"{cat}: {amount:.2f} UAH ({percentage:.1f}%)\n"

    return summary


async def generate_monthly_report(message: Message, year: int, month: int) -> None:
    """
    Generates and sends a monthly expense report with visualizations.
    """
    user_id = message.chat.id

    async with get_async_session() as session:
        # Get data (uses Redis cache from @redis_cache decorator)
        monthly_data = await get_monthly_expenses(session, user_id, year, month)

        if not monthly_data:
            await message.answer(f"No expenses for {calendar.month_name[month]} {year}")
            return

        # Check if we have cached image
        image_key = f"report_image:monthly:{user_id}:{year}:{month}"
        cached_image = await redis.get(image_key)

        if cached_image:
            await message.answer_photo(
                BufferedInputFile(cached_image, filename=f"monthly_report_{message.chat.id}.png"),
                caption=await generate_monthly_summary(monthly_data, year, month)
            )
            return

        # Process data for visualization
        df = pd.DataFrame([{
            'category': item['category'],
            'amount': item['total']
        } for item in monthly_data])

        # Create figure and visualization
        plt.figure(figsize=(20, 10))

        # Create bar plot with customization
        bars = plt.bar(df['category'], df['amount'], width=0.8)

        # Customize appearance
        plt.title(f'Monthly Expenses - {calendar.month_name[month]} {year}', pad=20, fontsize=14)
        plt.xlabel('Categories', fontsize=12, labelpad=10)
        plt.ylabel('Amount (UAH)', fontsize=12, labelpad=10)

        # Rotate x labels
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:,.0f}',
                     ha='center', va='bottom')

        # Ensure proper spacing
        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        image_data = buf.getvalue()
        plt.close()

        # Cache the image
        await redis.set(image_key, image_data, ex=900)  # 15 minutes cache

        # Generate summary and send report
        summary = await generate_monthly_summary(monthly_data, year, month)
        await message.answer_photo(
            BufferedInputFile(image_data, filename=f"monthly_report_{message.chat.id}.png"),
            caption=summary
        )


async def generate_monthly_summary(monthly_data: list, year: int, month: int) -> str:
    """Generate summary text for monthly report."""
    df = pd.DataFrame(monthly_data)
    total = df['total'].sum()

    category_details = []
    for _, row in df.iterrows():
        percentage = (row['total'] / total) * 100
        category_details.append(f"{row['category']}: {row['total']:.2f} UAH ({percentage:.1f}%)")

    return (
        f"Total for {calendar.month_name[month]} {year}: {total:.2f} UAH\n\n"
        "Breakdown by category:\n" + "\n".join(category_details)
    )


async def generate_daily_report(message: Message, year: int, month: int) -> None:
    """
    Generates and sends a daily expense report with visualizations.
    """
    user_id = message.chat.id

    async with get_async_session() as session:
        # Get data (uses Redis cache from @redis_cache decorator)
        daily_data = await get_daily_expenses(session, user_id, year, month)

        if not daily_data:
            await message.answer(f"No expenses found for {calendar.month_name[month]} {year}")
            return

        # Check if we have cached image for this data
        image_key = f"report_image:daily:{user_id}:{year}:{month}"
        cached_image = await redis.get(image_key)

        if cached_image:
            # Send cached image with fresh summary
            await message.answer_photo(
                BufferedInputFile(cached_image, filename=f"daily_report_{message.chat.id}.png"),
                caption=await generate_daily_summary(daily_data, year, month)
            )
            return

        # If no cache, generate new report
        df = pd.DataFrame([{
            'day': item['day'],
            'category': item['category'],
            'total': item['total']
        } for item in daily_data])

        # Get number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]

        # Create a complete DataFrame with all days
        all_days = pd.DataFrame({'day': range(1, days_in_month + 1)})

        # Merge with actual data
        complete_df = all_days.merge(df, on='day', how='left')
        complete_df['total'] = complete_df['total'].fillna(0)
        complete_df['category'] = complete_df['category'].fillna('')

        # Create pivot table
        pivot_table = complete_df.pivot_table(
            index='day',
            columns='category',
            values='total',
            fill_value=0
        )

        # Generate visualization
        plt.figure(figsize=(20, 10))
        ax = pivot_table.plot(kind='bar', stacked=True, width=0.8, figsize=(20, 10))
        plt.title(f'Daily Expenses - {calendar.month_name[month]} {year}', pad=20, fontsize=14)
        plt.xlabel('Day of Month', fontsize=12, labelpad=10)
        plt.ylabel('Amount (UAH)', fontsize=12, labelpad=10)

        # Set x-axis ticks and labels
        plt.xticks(range(days_in_month), range(1, days_in_month + 1), rotation=45, ha='right')

        # Add sum labels on top of bars
        daily_sums = pivot_table.sum(axis=1)
        for i, sum_value in enumerate(daily_sums):
            if sum_value > 0:  # Only show label if there are expenses
                plt.text(i, sum_value, f'{sum_value:,.0f}',
                         ha='center', va='bottom')

        # Adjust legend and add grid
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Ensure proper spacing
        plt.subplots_adjust(bottom=0.15, right=0.85)
        plt.tight_layout()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        image_data = buf.getvalue()
        plt.close()

        # Cache the image
        await redis.set(image_key, image_data, ex=900)  # 15 minutes cache

        # Generate summary
        summary = await generate_daily_summary(daily_data, year, month)

        # Send report
        await message.answer_photo(
            BufferedInputFile(image_data, filename=f"daily_report_{message.chat.id}.png"),
            caption=summary
        )


async def generate_daily_summary(daily_data: list, year: int, month: int) -> str:
    """Generate summary text for daily report."""
    df = pd.DataFrame(daily_data)
    total = df['total'].sum()
    daily_totals = df.groupby('day')['total'].sum()
    category_totals = df.groupby('category')['total'].sum()

    summary = f"Daily Report for {calendar.month_name[month]} {year}\n"
    summary += f"Total spent: {total:.2f} UAH\n\n"

    # Add category breakdown
    summary += "By category:\n"
    for cat, amount in category_totals.items():
        percentage = (amount / total) * 100
        summary += f"{cat}: {amount:.2f} UAH ({percentage:.1f}%)\n"

    # Add highest spending day
    if not daily_totals.empty:
        max_day = daily_totals.idxmax()
        summary += f"\nHighest spending day: {max_day} ({daily_totals[max_day]:.2f} UAH)"

    return summary