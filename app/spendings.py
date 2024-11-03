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
    description = State()


@router.callback_query(F.data.startswith("category_"))
async def spends(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.answer("Вы выбрали категорию трат")
        await state.set_state(Spendings.category)
        await state.update_data(category=callback_query.data)
        await state.set_state(Spendings.amount)
        await callback_query.message.reply("Введите количество потраченых денег")
    except Exception as e:
        print(e)
        await state.clear()
        await callback_query.message.answer("Что-то пошло не так поробуйте снова")


@router.message(Spendings.amount)
async def spends_amount(message: Message, state: FSMContext):
    try:
        amount = abs(float(message.text))
        await state.update_data(amount=amount)
        await state.set_state(Spendings.date)
        await message.reply("Введите дату траты через пробел")
    except Exception as e:
        print(e)
        await state.clear()
        await message.answer("Что-то пошло не так поробуйте снова")


@router.message(Spendings.date)
async def spends_date(message: Message, state: FSMContext):
    try:
        await state.update_data(date=datetime.strptime(message.text, "%d %m %Y"))
        await state.set_state(Spendings.description)
        await message.reply("Введите описание для потраченых денег")
    except Exception as e:
        print(e)
        await state.clear()
        await message.answer("Что-то пошло не так поробуйте снова")


@router.message(Spendings.description)
async def spends_date(message: Message, state: FSMContext):
    try:
        await state.update_data(description=message.text)
        data = await state.get_data()
        await message.reply(f'{data["category"]}, {data["date"]}, {data["amount"]}, {data["description"]}')
        await state.clear()
    except Exception as e:
        print(e)
        await state.clear()
        await message.answer("Что-то пошло не так поробуйте снова")
