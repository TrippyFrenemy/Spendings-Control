import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from config import API_TOKEN


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message()
async def echo(message: Message):
    await message.answer("Hello World!")
    await message.reply("How are you!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
