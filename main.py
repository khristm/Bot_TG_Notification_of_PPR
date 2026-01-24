import asyncio
from aiogram import Dispatcher, Bot
from database.database import async_session
from config import config
from database.init_db import init_db
from middleware import DbSessionMiddleware
from handlers.common import router as common_router
from handlers.parsing import router as parsing_router

async def main():
    await init_db()
    bot=Bot(token=config.token_bot)
    dp=Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())
