from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from keybords.common import month_user_keyboard


router=Router()

@router.callback_query(F.data=="view_schedule")
async def view_schedule(callback:CallbackQuery, session:AsyncSession):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(text="Выбери месяц который просматриваем:",reply_markup=await month_user_keyboard(session,callback.from_user.id))
