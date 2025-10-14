"""
Система уведомлений для Telegram бота
"""
import asyncio
import logging
from datetime import datetime
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.database import BotDatabase
from models.product import Product

class ParsingLogger:
    """Класс для управления логами парсинга в реальном времени"""
    
    def __init__(self, notification_service, user_id: int):
        self.notification_service = notification_service
        self.user_id = user_id
        self.log_message = None
        self.log_entries = []
        self.max_message_length = 4000
        self.update_count = 0
        self.max_updates = 5  # Максимум 5 обновлений сообщения
        self.total_shops = 0
        self.current_shop = 0
        
    async def start_logging(self):
        """Начинаем логирование - отправляем первое сообщение"""
        initial_text = "🚀 <b>Запуск парсинга</b>\n\n📋 <b>Лог процесса:</b>\n\n⏳ Инициализация..."
        
        self.log_message = await self.notification_service.send_message_to_user(
            self.user_id, initial_text
        )
        
        if self.log_message:
            self.log_entries.append("⏳ Инициализация...")
    
    def set_total_shops(self, total: int):
        """Устанавливаем общее количество магазинов"""
        self.total_shops = total
    
    async def add_log_entry(self, entry: str):
        """Добавляем новую запись в лог с ограничением обновлений"""
        if not self.log_message:
            return
            
        self.log_entries.append(entry)
        
        # Определяем, нужно ли обновлять сообщение
        should_update = False
        
        if self.update_count < self.max_updates:
            # Обновляем на ключевых этапах
            if ("📋 Найдено" in entry or 
                "🔍 Анализируем" in entry or 
                "🎉 Найдено" in entry or 
                "🧹 Очистка" in entry or
                "❌" in entry or
                "🛑" in entry):
                should_update = True
            
            # Или каждые 20% прогресса парсинга магазинов
            elif "🔄" in entry and self.total_shops > 0:
                self.current_shop += 1
                progress_percent = (self.current_shop / self.total_shops) * 100
                if progress_percent >= (self.update_count + 1) * 20:
                    should_update = True
        
        if should_update:
            await self._update_message()
            self.update_count += 1
    
    async def _update_message(self):
        """Обновляем сообщение в Telegram"""
        new_text = "🚀 <b>Запуск парсинга</b>\n\n📋 <b>Лог процесса:</b>\n\n"
        
        # Добавляем записи, следя за лимитом длины
        temp_entries = []
        temp_length = len(new_text)
        
        # Идем с конца, чтобы показать самые свежие записи
        for entry in reversed(self.log_entries):
            entry_length = len(entry) + 1
            if temp_length + entry_length > self.max_message_length:
                break
            temp_entries.insert(0, entry)
            temp_length += entry_length
        
        # Если не все записи поместились, добавляем индикатор
        if len(temp_entries) < len(self.log_entries):
            new_text += "...\n"
        
        new_text += "\n".join(temp_entries)
        
        # Обновляем сообщение с задержкой для избежания flood control
        import asyncio
        await asyncio.sleep(1)
        await self.notification_service.edit_message(
            self.user_id, 
            self.log_message.message_id, 
            new_text
        )
    
    async def finish_logging(self, total_new_products: int):
        """Завершаем логирование"""
        if total_new_products > 0:
            final_entry = f"✅ <b>Парсинг завершен!</b> Найдено {total_new_products} новых товаров"
        else:
            final_entry = "✅ <b>Парсинг завершен!</b> Новых товаров не найдено"
            
        await self.add_log_entry(final_entry)

class NotificationService:
    """Сервис для отправки уведомлений о новых товарах"""
    
    def __init__(self, bot: Bot, db: BotDatabase):
        self.bot = bot
        self.db = db
        self.max_message_length = 4000  # Лимит Telegram ~4096, оставляем запас
    
    async def send_long_message(self, user_id: int, message: str, parse_mode: str = "HTML") -> bool:
        """Отправка длинного сообщения с разбивкой на части"""
        if len(message) <= self.max_message_length:
            return await self.send_message_to_user(user_id, message, parse_mode)
        
        # Разбиваем сообщение на части
        parts = []
        current_part = ""
        
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 > self.max_message_length:
                if current_part:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    # Если одна строка слишком длинная, обрезаем её
                    parts.append(line[:self.max_message_length])
            else:
                current_part += line + '\n'
        
        if current_part:
            parts.append(current_part)
        
        # Отправляем части по очереди
        success = True
        for i, part in enumerate(parts):
            if i == 0:
                result = await self.send_message_to_user(user_id, part, parse_mode)
            else:
                part_with_header = f"📊 <b>Продолжение ({i+1}/{len(parts)})</b>\n\n{part}"
                result = await self.send_message_to_user(user_id, part_with_header, parse_mode)
            
            if not result:
                success = False
            
            # Небольшая задержка между сообщениями
            await asyncio.sleep(0.5)
        
        return success
    
    async def send_message_to_user(self, user_id: int, message: str, parse_mode: str = "HTML") -> bool:
        """Отправка сообщения конкретному пользователю"""
        try:
            sent_message = await asyncio.wait_for(
                self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=parse_mode
                ),
                timeout=30
            )
            return sent_message
        except asyncio.TimeoutError:
            logging.error(f"Таймаут отправки сообщения пользователю {user_id}")
            return False
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False

    async def edit_message(self, chat_id: int, message_id: int, new_text: str, parse_mode: str = "HTML") -> bool:
        """Редактирование существующего сообщения"""
        try:
            await asyncio.wait_for(
                self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=new_text,
                    parse_mode=parse_mode
                ),
                timeout=30
            )
            return True
        except asyncio.TimeoutError:
            logging.error(f"Таймаут редактирования сообщения")
            return False
        except Exception as e:
            logging.error(f"Ошибка редактирования сообщения: {e}")
            return False
    
    async def send_new_product_notification(self, product: Product) -> bool:
        """Отправка уведомления о новом товаре всем администраторам"""
        try:
            # Получаем список всех администраторов
            admins = await self.db.get_all_admins()
            
            if not admins:
                logging.warning("Нет администраторов для отправки уведомлений")
                return False
            
            # Формируем сообщение
            message_text = self._format_notification_message(product)
            
            # Отправляем уведомление каждому администратору
            sent_count = 0
            for admin_id, _ in admins:
                try:
                    await asyncio.wait_for(
                        self.bot.send_message(
                            chat_id=admin_id,
                            text=message_text,
                            parse_mode="HTML",
                            disable_web_page_preview=False
                        ),
                        timeout=30
                    )
                    sent_count += 1
                    logging.info(f"Уведомление отправлено администратору {admin_id}")
                    
                    # Задержка между сообщениями
                    await asyncio.sleep(0.5)
                    
                except asyncio.TimeoutError:
                    logging.error(f"Таймаут отправки администратору {admin_id}")
                except TelegramForbiddenError:
                    logging.warning(f"Администратор {admin_id} заблокировал бота")
                except TelegramBadRequest as e:
                    logging.error(f"Ошибка отправки администратору {admin_id}: {e}")
                except Exception as e:
                    logging.error(f"Неожиданная ошибка при отправке администратору {admin_id}: {e}")
            
            logging.info(f"Уведомление отправлено {sent_count} из {len(admins)} администраторов")
            return sent_count > 0
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о товаре: {e}")
            return False
    
    async def send_multiple_products_notification(self, products: List[Product]) -> bool:
        """Отправка уведомления о нескольких новых товарах"""
        if not products:
            return False
        
        try:
            # Получаем список всех администраторов
            admins = await self.db.get_all_admins()
            
            if not admins:
                logging.warning("Нет администраторов для отправки уведомлений")
                return False
            
            # Группируем товары по магазинам
            shops_products = {}
            for product in products:
                if product.shop_name not in shops_products:
                    shops_products[product.shop_name] = []
                shops_products[product.shop_name].append(product)
            
            # Отправляем уведомления по магазинам
            sent_count = 0
            for shop_name, shop_products in shops_products.items():
                message_text = self._format_multiple_products_message(shop_name, shop_products)
                
                # Отправляем каждому администратору с поддержкой длинных сообщений
                for admin_id, _ in admins:
                    try:
                        success = await self.send_long_message(admin_id, message_text)
                        if success:
                            sent_count += 1
                        
                    except Exception as e:
                        logging.error(f"Неожиданная ошибка при отправке администратору {admin_id}: {e}")
            
            logging.info(f"Уведомления о {len(products)} товарах отправлены")
            return sent_count > 0
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомлений о товарах: {e}")
            return False
    
    def _format_notification_message(self, product: Product) -> str:
        """Форматирование минимального сообщения о новом товаре согласно требованиям"""
        discovery_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Минимальное сообщение: заголовок, магазин, ссылка, время
        message = f"""🆕 <b>Найден новый товар в {product.shop_name}</b>

<a href="{product.url}">{product.title[:80]}{'...' if len(product.title) > 80 else ''}</a>

🕐 {discovery_time}"""
        
        return message
    
    def _format_multiple_products_message(self, shop_name: str, products: List[Product]) -> str:
        """Форматирование минимального сообщения о нескольких новых товарах"""
        discovery_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        message = f"""🆕 <b>Найдено {len(products)} новых товаров в {shop_name}</b>

🕐 {discovery_time}

"""
        
        # Показываем максимум 5 товаров в минимальном формате
        for i, product in enumerate(products[:5]):
            title = product.title[:60] + '...' if len(product.title) > 60 else product.title
            message += f"• <a href='{product.url}'>{title}</a>\n"
        
        if len(products) > 5:
            message += f"\n... и еще {len(products) - 5} товаров"
        
        return message
    
    async def send_parsing_started_notification(self, user_id: int = None) -> bool:
        """Уведомление о начале парсинга (только инициатору или всем админам)"""
        try:
            message = f"""🚀 <b>Запуск парсинга</b>

🔍 Начинаю поиск новых товаров..."""
            
            if user_id:
                # Отправляем только инициатору
                return await self.send_message_to_user(user_id, message)
            else:
                # Отправляем всем админам (автоматический запуск по расписанию)
                admins = await self.db.get_all_admins()
                if not admins:
                    return False
                
                for admin_id, _ in admins:
                    await self.send_message_to_user(admin_id, message)
                
                return True
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о начале парсинга: {e}")
            return False
    
    async def send_parsing_completed_notification(self, total_new_products: int, user_id: int = None) -> bool:
        """Уведомление о завершении парсинга (только инициатору или всем админам)"""
        try:
            if total_new_products > 0:
                message = f"""✅ <b>Парсинг завершен</b>

🆕 Найдено новых товаров: {total_new_products}"""
            else:
                message = f"""✅ <b>Парсинг завершен</b>

📭 Новых товаров не найдено"""
            
            if user_id:
                # Отправляем только инициатору
                return await self.send_message_to_user(user_id, message)
            else:
                # Отправляем всем админам (автоматический запуск по расписанию)
                admins = await self.db.get_all_admins()
                if not admins:
                    return False
                
                for admin_id, _ in admins:
                    await self.send_message_to_user(admin_id, message)
                
                return True
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о завершении парсинга: {e}")
            return False
    
    def _format_notification_message(self, product: Product) -> str:
        """Форматирование минимального сообщения о новом товаре согласно требованиям"""
        discovery_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Минимальное сообщение: заголовок, магазин, ссылка, время
        message = f"""🆕 <b>Найден новый товар в {product.shop_name}</b>

<a href="{product.url}">{product.title[:80]}{'...' if len(product.title) > 80 else ''}</a>

🕐 {discovery_time}"""
        
        return message
    
    def _format_multiple_products_message(self, shop_name: str, products: List[Product]) -> str:
        """Форматирование сообщения о нескольких новых товарах"""
        discovery_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        message = f"""🆕 <b>Найдено {len(products)} новых товаров в {shop_name}</b>

🕐 {discovery_time}

"""
        
        # Показываем все товары, но с ограничением длины
        for i, product in enumerate(products):
            title = product.title[:60] + '...' if len(product.title) > 60 else product.title
            message += f"• <a href='{product.url}'>{title}</a>\n"
        
        return message
    
    async def send_parsing_started_notification(self, user_id: int = None) -> bool:
        """Уведомление о начале парсинга (только инициатору или всем админам)"""
        try:
            message = f"""🚀 <b>Запуск парсинга</b>

🔍 Начинаю поиск новых товаров..."""
            
            if user_id:
                # Отправляем только инициатору
                return await self.send_message_to_user(user_id, message)
            else:
                # Отправляем всем админам (автоматический запуск по расписанию)
                admins = await self.db.get_all_admins()
                if not admins:
                    return False
                
                for admin_id, _ in admins:
                    await self.send_message_to_user(admin_id, message)
                
                return True
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о начале парсинга: {e}")
            return False
    
    async def send_parsing_completed_notification(self, total_new_products: int, user_id: int = None) -> bool:
        """Уведомление о завершении парсинга (только инициатору или всем админам)"""
        try:
            if total_new_products > 0:
                message = f"""✅ <b>Парсинг завершен</b>

🆕 Найдено новых товаров: {total_new_products}"""
            else:
                message = f"""✅ <b>Парсинг завершен</b>

📭 Новых товаров не найдено"""
            
            if user_id:
                # Отправляем только инициатору
                return await self.send_message_to_user(user_id, message)
            else:
                # Отправляем всем админам (автоматический запуск по расписанию)
                admins = await self.db.get_all_admins()
                if not admins:
                    return False
                
                for admin_id, _ in admins:
                    await self.send_message_to_user(admin_id, message)
                
                return True
            
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о завершении парсинга: {e}")
            return False