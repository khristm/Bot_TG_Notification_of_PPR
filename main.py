import asyncio
from datetime import datetime

from aiogram import Dispatcher, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import async_session
from config import config
from database.init_db import init_db
from middleware import DbSessionMiddleware, ExceptionsFromHandlers
from handlers.common import router as common_router
from handlers.parsing import router as parsing_router
from handlers.read import router as read_router
from database.database import dvijok
from handlers.delete import router as delete_router
from database.crud import get_list_today_tasks
from utils import everyday_check_to_msg

async def main():
    print(datetime.now(), " Инициализация БД ")
    await init_db()
    print(datetime.now()," Инициализация бота ")
    bot=Bot(token=config.token_bot)
    dp=Dispatcher()
    print(datetime.now()," Подключение мидлвеаров ")
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.update.middleware(ExceptionsFromHandlers(bot))
    print(datetime.now(), " Запуск проверки актуальных заданий ")
    async with async_session() as session:
        await everyday_check_to_msg(session,bot)
    print(datetime.now(), " Включение роутеров ")
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    dp.include_router(read_router)
    dp.include_router(delete_router)
    try:
        print(datetime.now()," Включение поллинга ")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dvijok.dispose()



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(datetime.now()," Отключено пользователем ")
    # async def test():
    #     async with async_session() as session:
    #         res = await get_list_today_tasks(session)
    #         print(f"Результат выборки {res}")
    #         print(f"номер задания:{res[0][0].Task.number} ид чата:{res[0][0][1]}")
    # asyncio.run(test())
