"""
Главный файл для запуска GUI приложения Etsy Parser
"""
import sys
import os
import logging
import traceback
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем обработчик ошибок если он существует
try:
    import error_handler
except ImportError:
    pass

def setup_logging():
    """Настройка системы логирования"""
    try:
        # Создаем директорию для логов
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / 'app.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    except Exception as e:
        print(f"Ошибка настройки логирования: {e}")
        return logging.getLogger(__name__)

logger = setup_logging()

def ensure_directories():
    """Создание необходимых директорий"""
    directories = ['logs', 'output']
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"✅ Директория {directory} готова")
        except Exception as e:
            logger.error(f"❌ Ошибка создания директории {directory}: {e}")
            raise

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    required_modules = [
        ('tkinter', 'tkinter'),
        ('selenium', 'selenium'),
        ('aiogram', 'aiogram'),
        ('requests', 'requests'),
        ('openpyxl', 'openpyxl')
    ]
    
    missing_modules = []
    for module_name, import_name in required_modules:
        try:
            __import__(import_name)
            logger.info(f"✅ Модуль {module_name} найден")
        except ImportError:
            missing_modules.append(module_name)
            logger.error(f"❌ Модуль {module_name} не найден")
    
    if missing_modules:
        error_msg = f"Отсутствуют необходимые модули: {', '.join(missing_modules)}\n\n"
        error_msg += "Установите их командой: pip install " + " ".join(missing_modules)
        raise ImportError(error_msg)

def main():
    """Главная функция запуска GUI"""
    try:
        print("🚀 Запуск Etsy Parser GUI")  # Дублируем в консоль
        logger.info("🚀 Запуск Etsy Parser GUI")
        
        # Проверяем зависимости
        logger.info("🔍 Проверка зависимостей...")
        check_dependencies()
        
        # Создаем необходимые директории
        logger.info("📁 Создание директорий...")
        ensure_directories()
        
        # Импортируем и запускаем GUI
        logger.info("🖥️ Запуск GUI...")
        from gui.main_window import MainWindow
        
        app = MainWindow()
        app.run()
        
    except ImportError as e:
        error_msg = f"Ошибка импорта модулей: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Ошибка зависимостей", error_msg)
            root.destroy()
        except:
            pass
        
        input("Нажмите Enter для выхода...")
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Критическая ошибка при запуске GUI: {e}"
        full_traceback = traceback.format_exc()
        
        logger.error(error_msg)
        logger.error(f"Полная трассировка: {full_traceback}")
        print(f"❌ {error_msg}")
        print(f"📋 Трассировка: {full_traceback}")
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # Скрываем главное окно
            
            messagebox.showerror(
                "Критическая ошибка",
                f"Не удалось запустить Etsy Parser GUI:\n\n{e}\n\n"
                f"Подробности сохранены в logs/app.log"
            )
            root.destroy()
        except:
            pass
        
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
        logger.info("Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        logger.error(f"Неожиданная ошибка: {e}")
        logger.error(f"Трассировка: {traceback.format_exc()}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)