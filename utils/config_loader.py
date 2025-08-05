"""
Утилита для загрузки конфигурации из config.txt и .env
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
        """Получение пути к файлу config.txt"""
        if getattr(sys, 'frozen', False):
            # Если приложение скомпилировано (PyInstaller)
            # config.txt должен быть рядом с .exe файлом
            return Path(sys.executable).parent / "config.txt"
        else:
            # Если запущено из исходников - в корне проекта
            return Path(__file__).parent.parent / "config.txt"
    
    def _get_env_path(self) -> Path:
        """Получение пути к файлу .env"""
        if getattr(sys, 'frozen', False):
            # Если приложение скомпилировано, .env может быть рядом с .exe
            exe_env = Path(sys.executable).parent / ".env"
            if exe_env.exists():
                return exe_env
        
        # В любом случае пробуем корень проекта
        return Path(__file__).parent.parent / ".env"
    
    def _load_config(self):
        """Загрузка конфигурации из файлов"""
        # Загружаем config.txt
        config_path = self._get_config_path()
        logger.info(f"Загрузка config.txt из: {config_path}")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            self.config_data[key.strip()] = value.strip()
                logger.info(f"Загружено {len(self.config_data)} параметров из config.txt")
            except Exception as e:
                logger.error(f"Ошибка чтения config.txt: {e}")
        else:
            logger.warning(f"Файл config.txt не найден: {config_path}")
        
        # Загружаем .env
        env_path = self._get_env_path()
        logger.info(f"Загрузка .env из: {env_path}")
        
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            # .env параметры не перезаписывают config.txt
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
        """Сохранение данных в config.txt"""
        config_path = self._get_config_path()
        
        try:
            # Создаем директорию если её нет
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                for key, value in data.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Конфигурация сохранена в {config_path}")
            
            # Перезагружаем конфигурацию
            self.reload()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения config.txt: {e}")
            raise
    
    def set_working_status(self, status: str):
        """Установка статуса работы парсера"""
        try:
            # Загружаем текущую конфигурацию
            current_data = self.get_all().copy()
            
            # Обновляем статус
            current_data["is_working"] = status
            
            # Сохраняем
            self.save_config_txt(current_data)
            
            logger.info(f"Статус работы установлен: {status}")
            
        except Exception as e:
            logger.error(f"Ошибка установки статуса работы: {e}")
            raise

# Глобальный экземпляр загрузчика конфигурации
config_loader = ConfigLoader()