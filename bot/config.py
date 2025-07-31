"""
Конфигурация Telegram бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    """Конфигурация бота"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")
    
    # Настройки по умолчанию для планировщика (согласно требованиям)
    DEFAULT_SCHEDULE_TIME = "10:00"  # 10:00 МСК по умолчанию
    DEFAULT_SCHEDULE_DAY = "monday"   # Понедельник по умолчанию
    TIMEZONE = "Europe/Moscow"

config = BotConfig()