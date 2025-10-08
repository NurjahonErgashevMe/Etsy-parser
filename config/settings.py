"""
Конфигурация приложения
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

def read_config_file() -> Dict[str, str]:
    """Читает конфигурацию из config-main.txt"""
    config_data = {}
    config_file = "config-main.txt"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()
        except Exception as e:
            print(f"Ошибка чтения config-main.txt: {e}")
    
    return config_data

def is_parser_working() -> bool:
    """Проверяет, запущен ли парсер согласно config-main.txt"""
    config_data = read_config_file()
    return config_data.get('is_working', 'stop').lower() == 'start'

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
    output_dir: str = "output"
    logs_dir: str = "logs"
    
    def is_working(self) -> bool:
        """Проверяет, запущен ли парсер"""
        return is_parser_working()
    
    # Google Sheets настройки
    google_sheets_enabled: bool = True
    google_sheets_credentials: str = "credentials.json"
    
    @property
    def google_sheets_spreadsheet_id(self) -> str:
        """Получает ID Google Sheets из config-main.txt"""
        config_data = read_config_file()
        return config_data.get('google_sheets_spreadsheet_id', '1X6R-ocA3xgybcq-sXgzltW56JnyPNZ_N2hlZn6uX42g')
    
    scheduler_enabled: bool = True
    
    telegram_bot_enabled: bool = True
    telegram_notifications_enabled: bool = True
    
    etsy: EtsyConfig = None
    
    def __post_init__(self):
        if self.etsy is None:
            self.etsy = EtsyConfig()

config = AppConfig()