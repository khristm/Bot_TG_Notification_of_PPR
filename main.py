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
from utils import everyday_check_to_msg
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def run_check_task(bot:Bot):
    async with async_session() as session:
        print(datetime.now()," Запуск проверки актуальных заданий по расписанию")
        await everyday_check_to_msg(session, bot)


async def notification(bot:Bot, scheduler:AsyncIOScheduler):
    scheduler.add_job(run_check_task, 'cron',
                      hour=config.time_check_tasks.hour,
                      minute=config.time_check_tasks.minute,
                      kwargs={"bot": bot})



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
    # async with async_session() as session:
    #     await everyday_check_to_msg(session,bot)
    scheduler = AsyncIOScheduler(timezone="Asia/Krasnoyarsk")
    await notification(bot, scheduler)
    scheduler.start()
    print(datetime.now(), " Включение роутеров ")
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    dp.include_router(read_router)
    dp.include_router(delete_router)
    try:
        print(datetime.now()," Включение поллинга ")
        await dp.start_polling(bot)
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()
        await dvijok.dispose()



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(datetime.now()," Отключено пользователем ")
