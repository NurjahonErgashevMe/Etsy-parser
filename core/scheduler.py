"""
Планировщик для автоматического запуска парсинга
"""
import schedule
import time
import logging
import pytz
from datetime import datetime
from core.monitor import EtsyMonitor
from config.settings import config

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
        
        # Настраиваем расписание на 4:00 МСК каждый день
        moscow_tz = pytz.timezone('Europe/Moscow')
        schedule.every().day.at("04:00").do(self.scheduled_job)
        
        # Показываем текущее время в МСК
        moscow_time = datetime.now(moscow_tz)
        logging.info(f"Планировщик запущен. Запуск каждый день в 4:00 МСК")
        logging.info(f"Текущее время МСК: {moscow_time.strftime('%Y-%m-%d %H:%M:%S')}")
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

def setup_logging():
    """Настройка логирования"""
    import os
    
    # Создаём папку для логов
    os.makedirs(config.logs_dir, exist_ok=True)
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(config.logs_dir, 'scheduler.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_logging()
    
    print("🚀 Запуск планировщика Etsy мониторинга")
    print("📅 Расписание: каждый день в 4:00 МСК")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    scheduler = EtsyScheduler()
    scheduler.start_scheduler()