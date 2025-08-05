"""
Интеграция Telegram бота с GUI
"""
import asyncio
import logging
import threading
import sys
from pathlib import Path
from typing import List
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import BotConfig
from bot.database import BotDatabase
from bot.handlers import router
from bot.notifications import NotificationService
from bot.scheduler_integration import BotScheduler
from utils.config_loader import config_loader

logger = logging.getLogger(__name__)

class TelegramBotGUI:
    """Класс для интеграции Telegram бота с GUI"""
    
    def __init__(self, bot_token: str, admin_ids: List[str]):
        self.bot_token = bot_token
        self.admin_ids = admin_ids
        self.bot = None
        self.dp = None
        self.db = None
        self.notification_service = None
        self.scheduler = None
        self.running = False
        self._stop_event = asyncio.Event()
    
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("Запуск Telegram бота из GUI...")
            
            # Сохраняем конфигурацию в config.txt
            config_data = {
                "BOT_TOKEN": self.bot_token,
                "ADMIN_ID": self.admin_ids[0] if self.admin_ids else ""
            }
            config_loader.save_config_txt(config_data)
            
            # Создаем конфигурацию
            config = BotConfig()
            config.reload()  # Перезагружаем после сохранения
            
            # Создаем бота и диспетчер
            self.bot = Bot(
                token=self.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            
            self.dp = Dispatcher()
            
            # Инициализируем базу данных
            self.db = BotDatabase("bot_database.db")
            await self.db.init_database()
            
            # Создаем сервис уведомлений
            self.notification_service = NotificationService(self.bot, self.db)
            
            # Создаем и запускаем планировщик
            self.scheduler = BotScheduler(self.notification_service, self.db)
            await self.scheduler.start_scheduler()
            
            # Добавляем middleware
            @self.dp.message.middleware()
            async def database_middleware(handler, event, data):
                data['db'] = self.db
                data['scheduler'] = self.scheduler
                return await handler(event, data)
            
            @self.dp.callback_query.middleware()
            async def callback_database_middleware(handler, event, data):
                data['db'] = self.db
                data['scheduler'] = self.scheduler
                return await handler(event, data)
            
            # Регистрируем роутер
            self.dp.include_router(router)
            
            self.running = True
            logger.info("Telegram бот запущен из GUI")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота из GUI: {e}")
            raise
    
    async def stop(self):
        """Остановка бота"""
        try:
            logger.info("Остановка Telegram бота из GUI...")
            
            self.running = False
            self._stop_event.set()
            
            # Останавливаем планировщик
            if self.scheduler:
                await self.scheduler.stop_scheduler()
            
            # Останавливаем диспетчер
            if self.dp:
                await self.dp.stop_polling()
            
            # Закрываем сессию бота
            if self.bot:
                await self.bot.session.close()
            
            logger.info("Telegram бот остановлен из GUI")
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота из GUI: {e}")
    
    def is_running(self) -> bool:
        """Проверка статуса бота"""
        return self.running
    
    async def send_test_message(self, message: str):
        """Отправка тестового сообщения"""
        if not self.bot or not self.running:
            raise Exception("Бот не запущен")
        
        try:
            for admin_id in self.admin_ids:
                await self.bot.send_message(chat_id=admin_id, text=message)
            logger.info("Тестовое сообщение отправлено")
        except Exception as e:
            logger.error(f"Ошибка отправки тестового сообщения: {e}")
            raise
    
    async def send_product_notification(self, product):
        """Отправка уведомления о товаре"""
        if not self.notification_service or not self.running:
            raise Exception("Бот не запущен или сервис уведомлений недоступен")
        
        try:
            # Используем сервис уведомлений для отправки товара
            await self.notification_service.send_new_products([product])
            logger.info("Уведомление о товаре отправлено")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о товаре: {e}")
            raise