from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from database.crud import create_user
from schemas import UserSchema
from sqlalchemy.ext.asyncio import AsyncSession

router=Router()

@router.message(Command("registration"))
async def registration(message: Message, session:AsyncSession):
    user_data=UserSchema(tg_id=str(message.from_user.id))
    res = await create_user(session=session ,user_data=user_data)
    if res:
        await message.answer("Ты добавлен")
    else:
        await message.answer("Ты уже есть в бд")