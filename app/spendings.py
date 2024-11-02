from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()


class Spendings(StatesGroup):
    category = State()
    amount = State()
    date = State()


@router.callback_query(F.data == "test1")
async def test1(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Вы выбрали категорию трат")
    await state.set_state(Spendings.category)
    await state.update_data(category=callback_query.data)
    await state.set_state(Spendings.amount)
    await callback_query.message.reply("Введите количество потраченых денег")


@router.message(Spendings.amount)
async def test1_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(Spendings.date)
    await message.reply("Введите дату траты через пробел")


@router.message(Spendings.date)
async def test1_date(message: Message, state: FSMContext):
    await state.update_data(date=datetime.strptime(message.text, "%d %m %Y"))
    data = await state.get_data()
    await message.reply(f'{data["category"]}, {data["date"]}, {data["amount"]}')
    await state.clear()
