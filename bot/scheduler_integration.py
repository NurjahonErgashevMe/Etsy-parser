"""
Интеграция планировщика с Telegram ботом
"""
import asyncio
import logging
import schedule
import time
import pytz
from datetime import datetime
from threading import Thread
from typing import Optional

from bot.database import BotDatabase
from bot.notifications import NotificationService
from core.monitor import EtsyMonitor
from models.product import Product

class BotScheduler:
    """Планировщик с интеграцией Telegram бота"""
    
    def __init__(self, notification_service: NotificationService, db: BotDatabase):
        self.notification_service = notification_service
        self.db = db
        self.monitor = EtsyMonitor()
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None
        self.moscow_tz = pytz.timezone('Europe/Moscow')
    
    async def scheduled_parsing_job(self, user_id: int = None):
        """Задача парсинга с уведомлениями"""
        try:
            logging.info("Запуск парсинга с уведомлениями")
            
            # Уведомляем о начале парсинга
            await self.notification_service.send_parsing_started_notification(user_id)
            
            # Запускаем мониторинг
            comparison_results = self.monitor.run_monitoring_cycle()
            
            # Собираем все новые товары
            all_new_products = []
            for result in comparison_results:
                if result.has_changes:
                    all_new_products.extend(result.new_products)
            
            # Отправляем уведомления о новых товарах (всегда всем админам)
            if all_new_products:
                await self.notification_service.send_multiple_products_notification(all_new_products)
                logging.info(f"Найдено и отправлено уведомлений о {len(all_new_products)} новых товарах")
            
            # Уведомляем о завершении парсинга
            await self.notification_service.send_parsing_completed_notification(len(all_new_products), user_id)
            
            logging.info("Парсинг завершен успешно")
            
        except Exception as e:
            logging.error(f"Ошибка в парсинге: {e}")
            
            # Уведомляем об ошибке
            try:
                error_message = f"""❌ <b>Ошибка парсинга</b>

🚨 Ошибка: {str(e)[:200]}

Проверьте логи для получения подробной информации."""
                
                if user_id:
                    # Отправляем только инициатору
                    await self.notification_service.send_message_to_user(user_id, error_message)
                else:
                    # Отправляем всем админам
                    admins = await self.db.get_all_admins()
                    for admin_id, _ in admins:
                        await self.notification_service.send_message_to_user(admin_id, error_message)
            except Exception:
                pass
    
    def _schedule_job_wrapper(self):
        """Обертка для запуска асинхронной задачи в синхронном планировщике"""
        try:
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем асинхронную задачу
            loop.run_until_complete(self.scheduled_parsing_job())
            
        except Exception as e:
            logging.error(f"Ошибка в обертке планировщика: {e}")
        finally:
            try:
                loop.close()
            except Exception:
                pass
    
    async def update_schedule(self):
        """Обновление расписания из базы данных"""
        try:
            # Очищаем старое расписание
            schedule.clear()
            
            # Получаем новые настройки
            schedule_time, schedule_day = await self.db.get_scheduler_settings()
            
            # Настраиваем новое расписание
            day_mapping = {
                "monday": schedule.every().monday,
                "tuesday": schedule.every().tuesday,
                "wednesday": schedule.every().wednesday,
                "thursday": schedule.every().thursday,
                "friday": schedule.every().friday,
                "saturday": schedule.every().saturday,
                "sunday": schedule.every().sunday
            }
            
            if schedule_day in day_mapping:
                day_mapping[schedule_day].at(schedule_time).do(self._schedule_job_wrapper)
                
                moscow_time = datetime.now(self.moscow_tz)
                logging.info(f"Расписание обновлено: {schedule_day} в {schedule_time} МСК")
                logging.info(f"Текущее время МСК: {moscow_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if schedule.jobs:
                    logging.info(f"Следующий запуск: {schedule.next_run()}")
            else:
                logging.error(f"Неизвестный день недели: {schedule_day}")
                
        except Exception as e:
            logging.error(f"Ошибка обновления расписания: {e}")
    
    def _scheduler_loop(self):
        """Основной цикл планировщика"""
        logging.info("Поток планировщика запущен")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logging.error(f"Ошибка в цикле планировщика: {e}")
                time.sleep(60)
        
        logging.info("Поток планировщика остановлен")
    
    async def start_scheduler(self):
        """Запуск планировщика"""
        if self.is_running:
            logging.warning("Планировщик уже запущен")
            return
        
        try:
            # Обновляем расписание из базы данных
            await self.update_schedule()
            
            # Запускаем планировщик в отдельном потоке
            self.is_running = True
            self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            moscow_time = datetime.now(self.moscow_tz)
            logging.info(f"Планировщик запущен в {moscow_time.strftime('%Y-%m-%d %H:%M:%S')} МСК")
            
            # Уведомляем администраторов о запуске
            try:
                admins = await self.db.get_all_admins()
                schedule_time, schedule_day = await self.db.get_scheduler_settings()
                
                day_names = {
                    "monday": "Понедельник",
                    "tuesday": "Вторник",
                    "wednesday": "Среда",
                    "thursday": "Четверг",
                    "friday": "Пятница",
                    "saturday": "Суббота",
                    "sunday": "Воскресенье"
                }
                
                startup_message = f"""🤖 <b>Бот запущен</b>

📅 <b>Расписание:</b>
• День: {day_names.get(schedule_day, schedule_day)}
• Время: {schedule_time}

✅ Мониторинг активен"""
                
                for admin_id, _ in admins:
                    await self.notification_service.send_message_to_user(admin_id, startup_message)
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления о запуске: {e}")
            
        except Exception as e:
            logging.error(f"Ошибка запуска планировщика: {e}")
            self.is_running = False
    
    async def stop_scheduler(self):
        """Остановка планировщика"""
        if not self.is_running:
            logging.warning("Планировщик уже остановлен")
            return
        
        try:
            self.is_running = False
            
            # Ждем завершения потока
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            # Очищаем расписание
            schedule.clear()
            
            logging.info("Планировщик остановлен")
            
            # Уведомляем администраторов об остановке
            try:
                admins = await self.db.get_all_admins()
                moscow_time = datetime.now(self.moscow_tz)
                
                shutdown_message = f"""🛑 <b>Бот остановлен</b>

❌ Мониторинг неактивен"""
                
                for admin_id, _ in admins:
                    await self.notification_service.send_message_to_user(admin_id, shutdown_message)
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления об остановке: {e}")
                
        except Exception as e:
            logging.error(f"Ошибка остановки планировщика: {e}")
    
    async def restart_scheduler(self):
        """Перезапуск планировщика с новыми настройками"""
        logging.info("Перезапуск планировщика...")
        await self.stop_scheduler()
        await asyncio.sleep(2)  # Небольшая пауза
        await self.start_scheduler()
    
    def is_scheduler_running(self) -> bool:
        """Проверка, запущен ли планировщик"""
        return self.is_running and (
            self.scheduler_thread is None or 
            self.scheduler_thread.is_alive()
        )