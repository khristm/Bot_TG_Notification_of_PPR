import datetime
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from pathlib import Path
import sys

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
    hello_msg:str
    run_exe:bool
    base_dir: Path|None = BASE_DIR
    model_config = SettingsConfigDict(env_file=BASE_DIR/".env")
    @model_validator(mode='after')
    def config_db_path(self):
        if not self.db_path.is_absolute():
            self.db_path = self.base_dir / self.db_path
        return self

config = Settings()

if __name__ == "__main__":
    print(config.db_path)
    print(config.token_bot)
    print(config.example_table)
    print(config.base_dir)