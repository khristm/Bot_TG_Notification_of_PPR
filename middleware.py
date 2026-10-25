from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramNetworkError
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from keybords.common import main_menu
from aiogram import Bot
from loguru import logger

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Открываем сессию из пула
        async with self.session_pool() as session:
            # Кладем сессию в словарь data, который прокидывается в хэндлеры
            data["session"] = session
            return await handler(event, data)

class ExceptionsFromHandlers(BaseMiddleware):
    """Мидлвеар для перехвата ошибок телеграмм апи в хэндлерах"""
    def __init__(self, bot:Bot):
        super().__init__()
        self.bot=bot
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramForbiddenError:
            pass
        except TelegramBadRequest as e:
            # logger.exception(e)
            error_msg=(str(e)).lower()
            chat = data.get("event_chat")
            chat_id = chat.id if chat else None
            if not chat_id:
                return logger.error(f"Нет в событии ид чата tg, ошибка: {error_msg}")
            if "message can't be edited" in error_msg:
                logger.error(f"Сообщение с мидллвеар: не смогли отредактировать старое сообщение "
                      f"ошибка: {e}")
                await self.bot.send_message(chat_id, "Истек срок возможности редактирования меню (ограничения ТГ), высылаю тебе новое")
                return await self.bot.send_message(chat_id=chat_id,text="Выбери пункт меню:",reply_markup=await main_menu())
            if "message can't be deleted" in error_msg:
                logger.error(f"Сообщение с мидллвеар: не смогли удалить сообщение "
                      f"ошибка: {e}")
                await self.bot.send_message(chat_id,"Истек срок возможности редактирования меню (ограничения ТГ), высылаю тебе новое")
                return await self.bot.send_message(chat_id=chat_id, text="Выбери пункт меню:",
                                                   reply_markup=await main_menu())
            return logger.error(f"Ошибка: {error_msg}, меню не перезапущено")
        except TelegramNetworkError as e:
            # logger.exception(e)
            logger.error(f"Сетевая ошибка: {e}")