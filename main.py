import asyncio
from aiogram import Dispatcher, Bot
from database.database import async_session
from config import config, custom_log, set_logger_config
from database.init_db import init_db
from middleware import DbSessionMiddleware, ExceptionsFromHandlers
from handlers.common import router as common_router
from handlers.parsing import router as parsing_router
from handlers.read import router as read_router
from database.database import dvijok
from handlers.delete import router as delete_router
from handlers.days_ppr import router as days_ppr_router
from utils import everyday_check_to_msg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import tgwsapiproxy
from aiogram.client.session.aiohttp import AiohttpSession
from loguru import logger

async def run_check_task(bot:Bot, admin_bot:Bot):
    async with async_session() as session:
        logger.info(" Запуск проверки актуальных заданий по расписанию")
        await everyday_check_to_msg(session, bot)
        try:
            await admin_bot.send_message(config.tg_admin,"Кузьма работает, выполнил рассылку уведомлений если они были")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу: {e}")


def notification(bot:Bot, scheduler:AsyncIOScheduler, admin_bot:Bot):
    scheduler.add_job(run_check_task, 'cron',
                      hour=config.time_check_tasks.hour,
                      minute=config.time_check_tasks.minute,
                      misfire_grace_time=600,
                      kwargs={"bot": bot, "admin_bot":admin_bot})

async def main():
    logger.info("Инициализация БД")
    await init_db()
    logger.info("Включение прокси")
    proxy_task = asyncio.create_task(tgwsapiproxy.run_proxy(config.proxy_ws_url))
    await asyncio.sleep(20.0)
    logger.info("Инициализация бота ")
    session = AiohttpSession(proxy=tgwsapiproxy.proxy_url())
    bot=Bot(token=config.token_bot, session=session)
    dp=Dispatcher()
    admin_bot=Bot(token=config.bot_admin, session=session)
    logger.info("Подключение мидлвеаров ")
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.update.middleware(ExceptionsFromHandlers(bot))
    logger.info("Включение планировщика заданий ")
    scheduler = AsyncIOScheduler(timezone="Asia/Krasnoyarsk")
    notification(bot, scheduler, admin_bot)
    scheduler.start()
    logger.info("Включение роутеров ")
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    dp.include_router(read_router)
    dp.include_router(delete_router)
    dp.include_router(days_ppr_router)
    try:
        logger.info("Включение поллинга ")
        while True:
            try:
                await dp.start_polling(bot,  timeout=40, polling_timeout=50)
            except (asyncio.TimeoutError, Exception) as polling_error:
                logger.warning(f"Сбой сети/поллинга: {polling_error}. Повторный запуск через 5 секунд...")
                await asyncio.sleep(5.0)
            else:
                break
    finally:
        proxy_task.cancel()
        try:
            await proxy_task
        except asyncio.CancelledError:
            logger.info("Прокси остановлен")
            pass
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()
        await admin_bot.session.close()
        await dvijok.dispose()
        logger.info("Все соединения закрыты")




if __name__ == '__main__':
    set_logger_config()
    tgwsapiproxy.log = custom_log
    logger.info(f"Директория БД из переменной окружения: {config.db_path}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Отключено пользователем ")
    except Exception as ex:
        logger.error(f"Остановка программы с ошибкой: {ex}")
