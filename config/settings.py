"""
Конфигурация приложения
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EtsyConfig:
    """Конфигурация для парсера Etsy (только браузер)"""
    base_url: str = "https://www.etsy.com"
    request_delay: int = 2  # Задержка между страницами
    max_retries: int = 3    # Количество попыток перезагрузки браузера
    page_load_timeout: int = 90  # Таймаут ожидания загрузки страницы (1.5 минуты)

@dataclass
class AppConfig:
    """Общая конфигурация приложения"""
    # Пути к файлам и папкам
    links_file: str = "links.txt"
    output_dir: str = "output"
    logs_dir: str = "logs"
    
    # Google Sheets настройки
    google_sheets_enabled: bool = True
    google_sheets_credentials: str = "credentials.json"
    google_sheets_spreadsheet_id: str = "1YT4JqyDd6s3n4MZVle2MxyrN9PDnHlmYxSsIhNUU6jY"
    
    # Настройки планировщика
    scheduler_enabled: bool = True
    # Планировщик запускается каждый день в 4:00 МСК
    
    # Настройки Telegram бота
    telegram_bot_enabled: bool = True
    telegram_notifications_enabled: bool = True
    
    etsy: EtsyConfig = None
    
    def __post_init__(self):
        if self.etsy is None:
            self.etsy = EtsyConfig()

config = AppConfig()