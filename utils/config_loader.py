"""
Утилита для загрузки конфигурации из config-main.txt и .env
"""
import os
import sys
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Класс для загрузки конфигурации"""
    
    def __init__(self):
        self.config_data = {}
        self._load_config()
    
    def _get_config_path(self) -> Path:
        """Получение пути к файлу config-main.txt"""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / "config-main.txt"
        else:
            return Path(__file__).parent.parent / "config-main.txt"
    
    def _get_env_path(self) -> Path:
        """Получение пути к файлу .env"""
        if getattr(sys, 'frozen', False):
            exe_env = Path(sys.executable).parent / ".env"
            if exe_env.exists():
                return exe_env
        
        return Path(__file__).parent.parent / ".env"
    
    def _load_config(self):
        """Загрузка конфигурации из файлов"""
        config_path = self._get_config_path()
        logger.info(f"Загрузка config-main.txt из: {config_path}")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            self.config_data[key.strip()] = value.strip()
                logger.info(f"Загружено {len(self.config_data)} параметров из config-main.txt")
            except Exception as e:
                logger.error(f"Ошибка чтения config-main.txt: {e}")
        else:
            logger.warning(f"Файл config-main.txt не найден: {config_path}")
        
        env_path = self._get_env_path()
        logger.info(f"Загрузка .env из: {env_path}")
        
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            if key.strip() not in self.config_data:
                                self.config_data[key.strip()] = value.strip()
                logger.info(f"Дополнительно загружено параметров из .env")
            except Exception as e:
                logger.error(f"Ошибка чтения .env: {e}")
        else:
            logger.warning(f"Файл .env не найден: {env_path}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Получение значения конфигурации"""
        return self.config_data.get(key, default)
    
    def get_required(self, key: str) -> str:
        """Получение обязательного значения конфигурации"""
        value = self.config_data.get(key)
        if not value:
            raise ValueError(f"Обязательный параметр {key} не найден в конфигурации")
        return value
    
    def has(self, key: str) -> bool:
        """Проверка наличия ключа в конфигурации"""
        return key in self.config_data
    
    def get_all(self) -> Dict[str, str]:
        """Получение всех параметров конфигурации"""
        return self.config_data.copy()
    
    def reload(self):
        """Перезагрузка конфигурации"""
        self.config_data.clear()
        self._load_config()
    
    def save_config_txt(self, data: Dict[str, str]):
        """Сохранение данных в config-main.txt (обновляет только переданные ключи)"""
        config_path = self._get_config_path()
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Загружаем существующие данные
            existing_data = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            existing_data[key.strip()] = value.strip()
            
            # Обновляем только переданные ключи
            existing_data.update(data)
            
            # Сохраняем все данные
            with open(config_path, 'w', encoding='utf-8') as f:
                for key, value in existing_data.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Конфигурация обновлена в {config_path}")
            self.reload()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения config-main.txt: {e}")
            raise
    
    def set_working_status(self, status: str):
        """Установка статуса работы парсера"""
        try:
            current_data = self.get_all().copy()
            current_data["is_working"] = status
            self.save_config_txt(current_data)
            logger.info(f"Статус работы установлен: {status}")
            
        except Exception as e:
            logger.error(f"Ошибка установки статуса работы: {e}")
            raise

config_loader = ConfigLoader()
