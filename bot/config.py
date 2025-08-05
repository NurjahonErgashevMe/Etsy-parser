"""
Конфигурация Telegram бота
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь для импорта utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import config_loader

# Загружаем .env для DATABASE_PATH
load_dotenv()

class BotConfig:
    """Конфигурация бота"""
    
    def __init__(self):
        # BOT_TOKEN и ADMIN_ID берем из config.txt через config_loader
        self.BOT_TOKEN = config_loader.get("BOT_TOKEN")
        
        admin_id_str = config_loader.get("ADMIN_ID", "0")
        try:
            self.ADMIN_ID = int(admin_id_str)
        except (ValueError, TypeError):
            self.ADMIN_ID = 0
        
        # DATABASE_PATH берем из .env
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")
        
        # Настройки по умолчанию для планировщика
        self.DEFAULT_SCHEDULE_TIME = "10:00"  # 10:00 МСК по умолчанию
        self.DEFAULT_SCHEDULE_DAY = "monday"   # Понедельник по умолчанию
        self.TIMEZONE = "Europe/Moscow"
    
    def reload(self):
        """Перезагрузка конфигурации"""
        config_loader.reload()
        self.__init__()

config = BotConfig()