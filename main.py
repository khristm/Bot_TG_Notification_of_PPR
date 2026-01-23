import asyncio
from aiogram import Dispatcher, Bot
from aiogram.types import Message
from database.database import async_session
import database.init_db
from config import config
from aiogram.filters import Command

from database.init_db import init_db
from middleware import DbSessionMiddleware
from handlers.common import router as common_router

async def main():
    await init_db()
    bot=Bot(token=config.token_bot)
    dp=Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.include_router(common_router)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())
