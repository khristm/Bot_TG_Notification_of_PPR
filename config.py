import datetime
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from pathlib import Path
import sys
from loguru import logger
import logging

def custom_log(msg):
    logger.info(msg)

if getattr(sys, 'frozen', False):
    # Если запущен exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Если запущен обычный .py
    BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    """Класс для объекта конфигурации,базовую директорию создаем после чтение .енв"""
    db_path: Path
    token_bot: str
    api_key: str
    time_check_tasks:datetime.time
    bot_admin: str
    tg_admin: str
    hello_msg:str
    proxy_ws_url:str
    path_log: Path = "work_log.log"
    log_level: str = "INFO"
    base_dir: Path|None = BASE_DIR
    model_config = SettingsConfigDict(env_file=BASE_DIR/".env")
    @model_validator(mode='after')
    def config_path(self):
        if not self.db_path.is_absolute():
            self.db_path = self.base_dir / self.db_path
            self.path_log = self.base_dir / self.path_log
        return self

config = Settings()

def set_logger_config():
    logger.remove()
    logger.add(
        config.path_log,             # Имя файла лога
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", # Чистый формат
        level=config.log_level,               # Записывать всё: от DEBUG до CRITICAL
        rotation="10 MB",            # Создать новый файл, если текущий превысил 10 МБ
        retention="5 days",          # Хранить логи только за последние 5 дней
        compression="zip",           # Старые логи автоматически сжимать в ZIP-архив
        encoding="utf-8"             # Корректная запись кириллицы
    )
    # перехват логгера aiogram
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)


class InterceptHandler(logging.Handler):
    """
    Стандартный перехватчик из документации loguru.
    Перенаправляет все системные логи (aiogram, aiohttp) в ваш красивый loguru.
    """
    def emit(self, record):
        # Получаем соответствующий уровень логирования из loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Находим место в коде, откуда пришел лог
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        # Отправляем очищенный лог в loguru
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Опционально: приглушаем внутренний отладочный флуд библиотек (оставляем только важные ошибки)
# logging.getLogger("aiogram").setLevel(logging.WARNING)
# logging.getLogger("aiohttp").setLevel(logging.ERROR)
