from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "")
async def test1(callback_query: CallbackQuery):
    await callback_query.answer("Вы выбрали категорию заработка")
    await callback_query.message.reply("")


