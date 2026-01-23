
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database.crud import create_user, update_chat_id
from schemas import UserSchema
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from keybords.common import registration_keyboard, main_menu

router=Router()

@router.message(Command("start"))
async def handler_start(message: Message):
    await message.answer(config.hello_msg)
    await message.answer(text="Нажми на кнопку регистрации",reply_markup=await registration_keyboard())


@router.callback_query(F.data=='registration')
async def registration(callback:CallbackQuery, session:AsyncSession):
    await callback.answer()
    user_data=UserSchema(tg_id=callback.from_user.id)
    res = await create_user(session=session ,user_data=user_data)
    await callback.message.delete()
    if res:
        await callback.message.answer("Регистрация успешно завершена")
    else:
        await callback.message.answer("Я тебя уже знал - похоже ты уже регистрировался когда-то раньше")
    await callback.message.answer("Выбери пункт меню:",reply_markup=await main_menu())

@router.message(Command("lock_chat"))
async def lock_chat(message:Message, session:AsyncSession):
    user=UserSchema(tg_id=message.from_user.id,chat_id=message.chat.id)
    res = await update_chat_id(session=session, user_data=user)
    if res:
        await message.answer("Чат привязан для оповещений")