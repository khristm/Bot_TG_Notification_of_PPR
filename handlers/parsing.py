from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.crud import create_user, update_chat_id
from schemas import UserSchema
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from keybords.common import registration_keyboard, main_menu
from keybords.parsing import get_date_schedule

router=Router()



@router.callback_query(F.data=='parsing')
async def get_month_for_parsing(callback:CallbackQuery, session:AsyncSession):
    await callback.message.delete()
    await callback.message.answer(text="Укажи месяц на который добавляем график:", reply_markup=await get_date_schedule())

@router.callback_query(F.data=='main_menu')
async def get_main_menu(callback:CallbackQuery, session:AsyncSession):
    await callback.message.delete()
    await callback.message.answer("Выбери пункт меню:",reply_markup=await main_menu())
