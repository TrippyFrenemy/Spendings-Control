import asyncio
import logging
from aiogram import Bot, Dispatcher

from app.handlers import register_all_handlers
from config import API_TOKEN
from app.db.models import async_main

# Set up logging configuration for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main entry point for the bot application.
    Initializes all necessary components and starts the bot.
    """
    # Initialize bot and dispatcher
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Register all message and callback handlers
    register_all_handlers(dp)

    # Initialize database and create tables if they don't exist
    await async_main()

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error during bot execution: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
