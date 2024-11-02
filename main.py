import asyncio

from aiogram import Bot, Dispatcher

from app.handlers import router as handlers_router
from app.spendings import router as spendings_router
from app.earns import router as earns_router
from config import API_TOKEN


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_routers(handlers_router, spendings_router, earns_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
