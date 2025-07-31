"""
Точка входа для запуска Telegram бота
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main as bot_main

def main():
    """Главная функция для запуска бота"""
    print("🤖 Запуск Telegram бота для мониторинга товаров")
    
    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()