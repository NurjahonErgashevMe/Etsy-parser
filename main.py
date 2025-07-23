"""
Точка входа для запуска планировщика автоматического мониторинга
"""
import os
import logging
from core.scheduler import EtsyScheduler

def main():
    """Главная функция для запуска планировщика"""
    # Создаём папку для логов
    os.makedirs('logs', exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    print("🚀 Etsy Monitor Scheduler")
    print("Запуск планировщика для автоматического мониторинга...")
    
    scheduler = EtsyScheduler()
    scheduler.start_scheduler()

if __name__ == "__main__":
    main()