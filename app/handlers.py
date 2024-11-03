from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

import app.keyboards as kb
import app.db.requests as rq

router = Router()


@router.message(CommandStart())
async def echo(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer("Привет!", reply_markup=kb.main)


@router.message(Command("help"))
async def help_message(message: Message):
    await message.reply("Help:")


@router.message(F.text == "Траты")
async def spendings(message: Message):
    await message.reply("Выберите категорию трат", reply_markup=kb.spendings)


@router.message(F.text == "Заработок")
async def earns(message: Message):
    await message.reply("Выберите категорию заработка", reply_markup=kb.earns)
