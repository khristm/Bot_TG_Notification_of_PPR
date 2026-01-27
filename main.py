import asyncio
from aiogram import Dispatcher, Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import async_session
from config import config
from database.init_db import init_db
from middleware import DbSessionMiddleware
from handlers.common import router as common_router
from handlers.parsing import router as parsing_router
from handlers.read import router as read_router
from database.database import dvijok
from handlers.delete import router as delete_router
from database.crud import get_list_today_tasks
from utils import everyday_check_to_msg

async def main():
    await init_db()
    bot=Bot(token=config.token_bot)
    dp=Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    async with async_session() as session:
        await everyday_check_to_msg(session,bot)
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    dp.include_router(read_router)
    dp.include_router(delete_router)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dvijok.dispose()



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Отключено пользователем")
    # async def test():
    #     async with async_session() as session:
    #         res = await get_list_today_tasks(session)
    #         print(f"Результат выборки {res}")
    #         print(f"номер задания:{res[0][0].Task.number} ид чата:{res[0][0][1]}")
    # asyncio.run(test())
