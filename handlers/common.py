from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database.crud import create_user, update_chat_id, delete_chat_id
from schemas import UserSchema
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from keybords.common import registration_keyboard, main_menu
from keybords.parsing import exit_to_menu_keyboard
from loguru import logger

router=Router()

@router.callback_query(F.data=='main_menu',F.message.chat.type == "private")
async def get_main_menu(callback:CallbackQuery, state:FSMContext):
    """Хэндлер возврата в главное меню, вызвает клаву главного меню"""
    await state.clear()
    logger.debug("Хэндлер главного меню")
    # await callback.message.delete()
    await callback.message.edit_text("Выбери пункт меню:",reply_markup=await main_menu())

@router.message(Command("start"),F.chat.type=="private")
async def handler_start(message: Message):
    """Хенделер первого запуска бота, инструкция и следом клава с кнопкой регистрации"""
    logger.debug("Хэндлер кнопки старт")
    await message.answer(config.hello_msg)
    await message.answer(text="Нажми на кнопку регистрации",reply_markup=await registration_keyboard())


@router.callback_query(F.data=='registration',F.message.chat.type == "private")
async def registration(callback:CallbackQuery, session:AsyncSession):
    """Хэндлер события нажатия клавиши регистрации, вызываем crud функцию бд, в конце вываливаем клаву главного меню"""
    await callback.answer()
    logger.debug(f"Хэндлер регистрации, пользователь: {callback.from_user.id}")
    user_data=UserSchema(tg_id=callback.from_user.id)
    res = await create_user(session=session ,user_data=user_data)
    # await callback.message.delete()
    if res:
        await callback.message.edit_text("Регистрация успешно завершена")
    else:
        await callback.message.edit_text("Я тебя узнал - похоже ты уже регистрировался когда-то раньше")
    await callback.message.answer("Выбери пункт меню:",reply_markup=await main_menu())

@router.message(Command("lock_chat"))
async def lock_chat(message:Message, session:AsyncSession):
    logger.debug(f"Хэндлер привязки чата, пользователь: {message.from_user.id}, чат: {message.chat.id}")
    user=UserSchema(tg_id=message.from_user.id,chat_id=message.chat.id)
    res = await update_chat_id(session=session, user_data=user)
    if res:
        await message.answer("Чат привязан для оповещений")
    else:
        await message.answer("Мы с тобой не знакомы, твою команду выполнить не могу")

@router.callback_query(F.data=='reset_chat_id',F.message.chat.type == "private")
async def reset_chat_id(callback:CallbackQuery, session:AsyncSession):
    logger.debug(f"Хэндлер сброса чата, пользователь: {callback.from_user.id}")
    res = await delete_chat_id(session,callback.from_user.id)
    if res:
        await callback.message.edit_text("Чат оповещений отвязан", reply_markup=await exit_to_menu_keyboard())
    else:
        await callback.message.edit_text("Что-то пошло не так, попробуй позже", reply_markup=await exit_to_menu_keyboard())


