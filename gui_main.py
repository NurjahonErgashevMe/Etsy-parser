"""
Главный файл для запуска GUI приложения Etsy Parser
"""
import sys
import os
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Консоль остается видимой для отладки

# Настройка логирования (общая система)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def ensure_directories():
    """Создание необходимых директорий"""
    directories = ['logs', 'output']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Директория {directory} готова")

def main():
    """Главная функция запуска GUI"""
    try:
        print("🚀 Запуск Etsy Parser GUI")  # Дублируем в консоль
        logger.info("🚀 Запуск Etsy Parser GUI")
        
        # Создаем необходимые директории
        ensure_directories()
        
        # Импортируем и запускаем GUI
        from gui.main_window import MainWindow
        
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске GUI: {e}")
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно
        
        messagebox.showerror(
            "Критическая ошибка",
            f"Не удалось запустить Etsy Parser GUI:\n\n{e}\n\n"
            f"Проверьте логи в папке logs/ для получения подробной информации."
        )
        
        sys.exit(1)

if __name__ == "__main__":
    main()