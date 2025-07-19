"""
Планировщик для автоматического запуска парсинга
"""
import schedule
import time
import logging
from datetime import datetime
from main import EtsyMonitor
from config import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

class EtsyScheduler:
    """Планировщик для автоматического мониторинга"""
    
    def __init__(self):
        self.monitor = EtsyMonitor()
        self.is_running = False
    
    def scheduled_job(self):
        """Задача для планировщика"""
        try:
            logging.info("Запуск запланированного мониторинга")
            self.monitor.run_monitoring_cycle()
            logging.info("Запланированный мониторинг завершен успешно")
            
        except Exception as e:
            logging.error(f"Ошибка в запланированном мониторинге: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if not config.scheduler_enabled:
            logging.info("Планировщик отключен в конфигурации")
            return
        
        # Настраиваем расписание
        schedule.every(config.check_interval_hours).hours.do(self.scheduled_job)
        
        logging.info(f"Планировщик запущен. Интервал: {config.check_interval_hours} часов")
        logging.info(f"Следующий запуск: {schedule.next_run()}")
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
                
        except KeyboardInterrupt:
            logging.info("Планировщик остановлен пользователем")
        except Exception as e:
            logging.error(f"Ошибка планировщика: {e}")
        finally:
            self.is_running = False
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.is_running = False
        logging.info("Планировщик остановлен")

def main():
    """Главная функция для запуска планировщика"""
    import os
    os.makedirs('logs', exist_ok=True)
    
    scheduler = EtsyScheduler()
    
    print("Etsy Monitor Scheduler")
    print("1. Запустить разовый мониторинг")
    print("2. Запустить планировщик")
    print("3. Выход")
    
    choice = input("Выберите опцию (1-3): ").strip()
    
    if choice == "1":
        monitor = EtsyMonitor()
        monitor.run_monitoring_cycle()
    elif choice == "2":
        scheduler.start_scheduler()
    elif choice == "3":
        print("До свидания!")
    else:
        print("Неверный выбор")

if __name__ == "__main__":
    main()