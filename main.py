import asyncio
from aiogram import Dispatcher, Bot
from aiogram.types import Message
from database.database import async_session
from config import config
from aiogram.filters import Command
from middleware import DbSessionMiddleware
from handlers.registration import router as registration_router

async def main():
    bot=Bot(token=config.token_bot)
    dp=Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    @dp.message(Command("start"))
    async def handler_start(message: Message):
        await message.answer(config.hello_msg)
    dp.include_router(registration_router)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())
