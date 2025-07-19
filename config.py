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
    
    # Настройки для будущих фич
    telegram_bot_token: str = ""
    google_sheets_credentials: str = ""
    
    # Настройки планировщика
    scheduler_enabled: bool = False
    check_interval_hours: int = 24
    
    etsy: EtsyConfig = None
    
    def __post_init__(self):
        if self.etsy is None:
            self.etsy = EtsyConfig()

# Глобальный экземпляр конфигурации
config = AppConfig()