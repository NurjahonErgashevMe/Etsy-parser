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
import os

class ParserLock:
    """Класс для управления блокировкой парсера через config.txt"""
    
    def __init__(self):
        self.config_file = "config.txt"
    
    def is_running(self) -> bool:
        """Проверяет, запущен ли парсер согласно config.txt"""
        from config.settings import is_parser_working
        return is_parser_working()
    
    def set_working(self):
        """Устанавливает статус 'start' в config.txt"""
        self._update_config_value("is_working", "start")
    
    def set_stopped(self):
        """Устанавливает статус 'stop' в config.txt"""
        self._update_config_value("is_working", "stop")
    
    def get_status(self) -> str:
        """Получает текущий статус из config.txt"""
        from config.settings import read_config_file
        config_data = read_config_file()
        return config_data.get('is_working', 'stop')
    
    def _update_config_value(self, key: str, value: str):
        """Обновляет значение в config.txt"""
        try:
            # Читаем текущий конфиг
            lines = []
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Обновляем или добавляем значение
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"{key}={value}\n")
            
            # Записываем обратно
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        except Exception as e:
            logging.error(f"Ошибка обновления config.txt: {e}")
    
    def force_stop(self):
        """Принудительно останавливает парсер"""
        try:
            self.set_stopped()
            logging.info("Парсер принудительно остановлен")
            return True
        except Exception as e:
            logging.error(f"Ошибка принудительной остановки: {e}")
            return False

class LoggingEtsyMonitor:
    """Обертка для EtsyMonitor с поддержкой логирования"""
    
    def __init__(self, monitor: EtsyMonitor, logger=None):
        self.monitor = monitor
        self.logger = logger
    
    def log_sync(self, message: str):
        """Добавляет запись в лог синхронно"""
        if self.logger:
            # Сохраняем сообщение для последующей отправки
            if not hasattr(self, 'pending_logs'):
                self.pending_logs = []
            
            self.pending_logs.append(message)
            logging.info(f"LOG: {message}")  # Дублируем в обычные логи
    
    async def flush_logs(self):
        """Отправляет все накопленные логи"""
        if self.logger and hasattr(self, 'pending_logs'):
            for log_message in self.pending_logs:
                try:
                    await self.logger.add_log_entry(log_message)
                except Exception as e:
                    logging.error(f"Ошибка отправки лога: {e}")
            
            self.pending_logs.clear()
    
    def run_monitoring_cycle_with_logging(self):
        """Запуск мониторинга с логированием без двойного парсинга"""
        try:
            # Получаем ссылки из Google Sheets
            links = self.monitor.data_service.load_shop_urls()
            
            if not links:
                self.log_sync("❌ Не удалось получить ссылки из Google Sheets")
                return []
            
            self.log_sync(f"📋 Найдено {len(links)} магазинов в Google Sheets")
            
            # Создаём папку для текущего сеанса парсинга
            parsing_dir = self.monitor.data_service.start_parsing_session()
            
            # Парсим все магазины с логированием
            all_shop_products = self.parse_all_shops_with_logging(links)
            
            # Проверяем, не был ли парсинг остановлен принудительно
            from config.settings import is_parser_working
            if not is_parser_working():
                self.log_sync("🛑 Парсинг был остановлен принудительно")
                return []
            
            if not all_shop_products:
                self.log_sync("❌ Не удалось получить данные ни от одного магазина")
                return []
            
            self.log_sync("🔍 Анализируем новые товары...")
            
            # Сохраняем результаты в JSON
            results_file = self.monitor.data_service.save_results_to_json(all_shop_products)
            
            # Сравниваем с предыдущими результатами
            current_results = {}
            for shop_name, products in all_shop_products.items():
                current_results[shop_name] = {product.listing_id: product.url for product in products}
            
            # Находим новые товары
            new_products_dict = self.monitor.data_service.compare_all_shops_results(current_results)
            
            # Сохраняем финальные результаты
            final_results_file = self.monitor.data_service.save_results_with_new_products(all_shop_products, new_products_dict)
            
            # Формируем результаты для бота
            comparison_results = []
            
            for shop_name, products in all_shop_products.items():
                # Находим новые товары для этого магазина
                new_products_for_shop = []
                for product in products:
                    if product.listing_id in new_products_dict:
                        new_products_for_shop.append(product)
                
                # Создаем объект сравнения
                from models.product import ShopComparison
                comparison = ShopComparison(
                    shop_name=shop_name,
                    new_products=new_products_for_shop,
                    removed_products=[],
                    total_current=len(products),
                    total_previous=len(products) - len(new_products_for_shop),
                    comparison_date=None
                )
                
                comparison_results.append(comparison)
            
            # Логируем итоги
            total_new = len(new_products_dict)
            if total_new > 0:
                self.log_sync(f"🎉 Найдено {total_new} новых товаров!")
            else:
                self.log_sync("📭 Новых товаров не найдено")
            
            # Очищаем всю output папку
            if self.monitor.data_service.cleanup_output_folder():
                self.log_sync("🧹 Очистка завершена")
            
            return comparison_results
            
        except Exception as e:
            self.log_sync(f"❌ Критическая ошибка: {str(e)[:100]}")
            logging.error(f"Критическая ошибка в мониторинге: {e}")
            return []
    
    def parse_all_shops_with_logging(self, urls):
        """Парсит все магазины с логированием прогресса"""
        all_shop_products = {}
        
        for i, url in enumerate(urls, 1):
            # Проверяем, не был ли парсинг остановлен принудительно
            from config.settings import is_parser_working
            if not is_parser_working():
                self.log_sync("🛑 Парсинг остановлен пользователем")
                break
            
            try:
                shop_name = self.monitor.parser.get_shop_name_from_url(url)
                self.log_sync(f"🔄 [{i}/{len(urls)}] Парсим: {shop_name}")
                
                # Парсим магазин
                products = self.monitor.parser.parse_shop_page(url)
                
                if products:
                    all_shop_products[shop_name] = products
                    
                    # Сохраняем данные
                    filename = self.monitor.data_service.save_products_to_excel(products, shop_name)
                    
                    self.log_sync(f"✅ {shop_name}: {len(products)} товаров")
                else:
                    self.log_sync(f"⚠️ {shop_name}: не удалось получить товары")
                
            except Exception as e:
                shop_name = self.monitor.parser.get_shop_name_from_url(url) if url else "Unknown"
                self.log_sync(f"❌ Ошибка в {shop_name}: {str(e)[:50]}")
                logging.error(f"Ошибка парсинга {url}: {e}")
        
        return all_shop_products



class BotScheduler:
    """Планировщик с интеграцией Telegram бота"""
    
    def __init__(self, notification_service: NotificationService, db: BotDatabase):
        self.notification_service = notification_service
        self.db = db
        self.monitor = EtsyMonitor()
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.parser_lock = ParserLock()
    
    async def scheduled_parsing_job(self, user_id: int = None):
        """Задача парсинга с уведомлениями"""
        logger = None
        
        # Проверяем блокировку парсера
        if self.parser_lock.is_running():
            error_msg = "⚠️ Парсер уже запущен! Дождитесь завершения текущего процесса."
            if user_id:
                await self.notification_service.send_message_to_user(user_id, error_msg)
            logging.warning("Попытка запуска парсера во время работы другого процесса")
            return
        
        # Устанавливаем блокировку
        self.parser_lock.set_working()
        
        try:
            logging.info("Запуск парсинга с уведомлениями")
            
            # Если есть user_id, создаем логгер для детального отслеживания
            if user_id:
                from bot.notifications import ParsingLogger
                logger = ParsingLogger(self.notification_service, user_id)
                await logger.start_logging()
            else:
                # Для автоматического парсинга отправляем простое уведомление всем
                await self.notification_service.send_parsing_started_notification(user_id)
            
            # Запускаем мониторинг с логированием
            if logger:
                comparison_results = await self.run_monitoring_with_logging(logger)
            else:
                # Для автоматического запуска используем обычный монитор
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
            
            # Завершаем логирование или отправляем уведомление
            if logger:
                await logger.finish_logging(len(all_new_products))
            else:
                await self.notification_service.send_parsing_completed_notification(len(all_new_products), user_id)
            
            logging.info("Парсинг завершен успешно")
            
        except Exception as e:
            logging.error(f"Ошибка в парсинге: {e}")
            
            # Уведомляем об ошибке
            try:
                error_message = f"""❌ <b>Ошибка парсинга</b>

🚨 Ошибка: {str(e)[:200]}

Проверьте логи для получения подробной информации."""
                
                if logger:
                    await logger.add_log_entry(f"❌ Ошибка: {str(e)[:100]}")
                elif user_id:
                    await self.notification_service.send_message_to_user(user_id, error_message)
                else:
                    # Отправляем всем админам
                    admins = await self.db.get_all_admins()
                    for admin_id, _ in admins:
                        await self.notification_service.send_message_to_user(admin_id, error_message)
            except Exception:
                pass
        finally:
            # Снимаем блокировку
            self.parser_lock.set_stopped()
            logging.info("Блокировка парсера снята")
    
    async def run_monitoring_with_logging(self, logger=None):
        """Запуск мониторинга с детальным логированием"""
        try:
            if logger:
                await logger.add_log_entry("🔍 Начинаем сканирование магазинов...")
            
            # Используем реальный EtsyMonitor с логированием
            comparison_results = await self.run_real_monitoring_with_logging(logger)
            
            return comparison_results
            
        except Exception as e:
            if logger:
                await logger.add_log_entry(f"❌ Критическая ошибка: {str(e)[:100]}")
            raise e
    
    async def run_real_monitoring_with_logging(self, logger=None):
        """Запуск реального мониторинга с логированием"""
        try:
            # Создаем кастомный монитор с логированием
            custom_monitor = LoggingEtsyMonitor(self.monitor, logger)
            
            # Запускаем мониторинг с логированием в отдельном потоке
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(custom_monitor.run_monitoring_cycle_with_logging)
                comparison_results = future.result()
            
            # Отправляем накопленные логи
            await custom_monitor.flush_logs()
            
            return comparison_results
            
        except Exception as e:
            logging.error(f"Ошибка в реальном мониторинге: {e}")
            if logger:
                await logger.add_log_entry(f"❌ Ошибка мониторинга: {str(e)[:100]}")
            return []
    
    def extract_shop_name(self, url: str) -> str:
        """Извлекает название магазина из URL"""
        try:
            if 'etsy.com/shop/' in url:
                return url.split('/shop/')[1].split('/')[0].split('?')[0]
            else:
                return url.split('//')[1].split('/')[0][:20]
        except:
            return "Unknown Shop"
    

    
    def _schedule_job_wrapper(self):
        """Обертка для запуска асинхронной задачи в синхронном планировщике"""
        try:
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем асинхронную задачу (без user_id для автоматического запуска)
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