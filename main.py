import asyncio
from aiogram import Dispatcher, Bot
from database.database import async_session
from config import config, custom_log, set_logger_config
from database.init_db import init_db
from middleware import DbSessionMiddleware, ExceptionsFromHandlers
from handlers.common import router as common_router
from handlers.parsing_tasks import router as parsing_router
from handlers.view_tasks import router as read_router
from handlers.workers import router as workers_router
from database.database import dvijok
from handlers.delete_tasks import router as delete_router
from handlers.days_ppr import router as days_ppr_router
from utils import everyday_check_to_msg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import tgwsapiproxy
from aiogram.client.session.aiohttp import AiohttpSession
from loguru import logger

async def run_check_task(bot:Bot, admin_bot:Bot):
    async with async_session() as session:
        logger.info(" Запуск проверки актуальных заданий по расписанию")
        result = await everyday_check_to_msg(session, bot)
        if result:
            text = "Кузьма работает, попытался выполнить рассылку уведомлений если они были"
        else:
            text = "Кузьма работает, но при проверке заданий на сутки вылетел с ошибкой"
        retry = 3
        i = 1
        while True:
            try:
                await admin_bot.send_message(config.tg_admin,text)
                break
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу: {e}, попытка: {i}")
                if retry == i:
                    logger.exception(e)
                    break
                i += 1
                await asyncio.sleep(3)




def notification(bot:Bot, scheduler:AsyncIOScheduler, admin_bot:Bot):
    scheduler.add_job(run_check_task, 'cron',
                      hour=config.time_check_tasks.hour,
                      minute=config.time_check_tasks.minute,
                      misfire_grace_time=600,
                      kwargs={"bot": bot, "admin_bot":admin_bot})

async def main():
    logger.info("Инициализация БД")
    await init_db()
    if config.proxy_ws_url:
        logger.info("Включение прокси")
        proxy_task = asyncio.create_task(tgwsapiproxy.run_proxy(config.proxy_ws_url))
    else:
        logger.info("Прокси не указан в переменной окружения, запуск в обычном режиме")
        proxy_task = None
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
    dp.include_router(workers_router)
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
        if proxy_task:
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
        logger.info("Отключено пользователем ")
    except Exception as ex:
        logger.error(f"Остановка программы с ошибкой: {ex}")
