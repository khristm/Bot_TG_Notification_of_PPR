import asyncio
from datetime import datetime
from aiogram import Dispatcher, Bot
from database.database import async_session
from config import config
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
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image
import ctypes
import tgwsapiproxy
from aiogram.client.session.aiohttp import AiohttpSession

async def run_check_task(bot:Bot, admin_bot:Bot):
    async with async_session() as session:
        print(datetime.now()," Запуск проверки актуальных заданий по расписанию")
        await everyday_check_to_msg(session, bot)
        try:
            await admin_bot.send_message(config.tg_admin,"Кузьма работает, выполнил рассылку уведомлений если они были")
        except Exception as e:
            print(f"Ошибка отправки уведомления админу: {e}")


async def notification(bot:Bot, scheduler:AsyncIOScheduler, admin_bot:Bot):
    scheduler.add_job(run_check_task, 'cron',
                      hour=config.time_check_tasks.hour,
                      minute=config.time_check_tasks.minute,
                      misfire_grace_time=600,
                      kwargs={"bot": bot, "admin_bot":admin_bot})

async def main():
    print(datetime.now(), " Инициализация БД ")
    await init_db()
    print(datetime.now()," Инициализация бота ")
    proxy_task = asyncio.create_task(tgwsapiproxy.run_proxy(config.proxy_ws_url))
    await asyncio.sleep(5.0)
    session = AiohttpSession(proxy=tgwsapiproxy.proxy_url())
    bot=Bot(token=config.token_bot, session=session)
    dp=Dispatcher()
    admin_bot=Bot(token=config.bot_admin, session=session)
    print(datetime.now()," Подключение мидлвеаров ")
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.update.middleware(ExceptionsFromHandlers(bot))
    print(datetime.now(), " Включение планировщика заданий ")
    scheduler = AsyncIOScheduler(timezone="Asia/Krasnoyarsk")
    await notification(bot, scheduler, admin_bot)
    scheduler.start()
    print(datetime.now(), " Включение роутеров ")
    dp.include_router(common_router)
    dp.include_router(parsing_router)
    dp.include_router(read_router)
    dp.include_router(delete_router)
    dp.include_router(days_ppr_router)
    try:
        print(datetime.now()," Включение поллинга ")
        await dp.start_polling(bot)
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()
        await dvijok.dispose()
        proxy_task.cancel()

"""Ниже код для запуска из под exe в windows"""
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

def get_console_handle():
    return kernel32.GetConsoleWindow()

def toggle_console(icon, item):
    hwnd = get_console_handle()
    if user32.IsWindowVisible(hwnd):
        user32.ShowWindow(hwnd, 0)
    else:
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)

def quit_app(icon):
    icon.stop()
    import os; os._exit(0)

def run_bot():
    asyncio.run(main())


if __name__ == '__main__':
    print(f"Директория БД из переменной окружения: {config.db_path}")
    if config.run_exe:
        print("Запуск в системном трее")
        hwnd = get_console_handle()
        if user32.IsWindowVisible(hwnd):
            user32.ShowWindow(hwnd, 0)
        icon=Image.open(config.base_dir/"icon.png")
        menu=Menu(MenuItem('Показать/Скрыть консоль', toggle_console, default=True),
                            MenuItem('Выход', quit_app))
        tray_exe=Icon("Bot",icon,"Кузьма бот",menu)

        threading.Thread(target=run_bot,daemon=True).start()
        tray_exe.run()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print(datetime.now()," Отключено пользователем ")
