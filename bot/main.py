"""
Главный файл Telegram бота
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.database import BotDatabase
from bot.handlers import router
from bot.notifications import NotificationService
from bot.scheduler_integration import BotScheduler
from bot.analytics_scheduler import AnalyticsScheduler

async def setup_bot_database(db: BotDatabase):
    """Настройка базы данных бота"""
    await db.init_database()
    
    # Главный администратор берется из .env, дополнительные - из БД
    logging.info(f"Главный администратор из .env: {config.ADMIN_ID}")

async def main():
    """Главная функция бота"""
    # Настройка логирования (общая система)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Проверяем конфигурацию
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен в переменных окружения")
        return
    
    if not config.ADMIN_ID:
        logging.error("ADMIN_ID не установлен в переменных окружения")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Инициализируем базу данных
    db = BotDatabase(config.DATABASE_PATH)
    await setup_bot_database(db)
    
    # Создаем сервис уведомлений
    notification_service = NotificationService(bot, db)
    
    # Создаем и запускаем планировщик парсинга
    logging.info("Создание планировщика парсинга...")
    scheduler = BotScheduler(notification_service, db)
    await scheduler.start_scheduler()
    
    # Создаем и запускаем планировщик аналитики
    logging.info("Создание планировщика аналитики...")
    analytics_scheduler = AnalyticsScheduler(notification_service, db)
    logging.info(f"analytics_scheduler создан: {analytics_scheduler}")
    await analytics_scheduler.start_scheduler()
    logging.info(f"Оба планировщика запущены. analytics_scheduler: {analytics_scheduler}")
    
    # Добавляем зависимости в middleware
    @dp.message.middleware()
    async def database_middleware(handler, event, data):
        data['db'] = db
        data['scheduler'] = scheduler
        data['analytics_scheduler'] = analytics_scheduler
        logging.debug(f"Message middleware: analytics_scheduler={analytics_scheduler}")
        return await handler(event, data)
    
    @dp.callback_query.middleware()
    async def callback_database_middleware(handler, event, data):
        data['db'] = db
        data['scheduler'] = scheduler
        data['analytics_scheduler'] = analytics_scheduler
        logging.debug(f"Callback middleware: analytics_scheduler={analytics_scheduler}")
        return await handler(event, data)
    
    logging.info(f"Middleware настроен. analytics_scheduler: {analytics_scheduler}")
    
    # Регистрируем роутер
    dp.include_router(router)
    
    # Запускаем бота
    try:
        logging.info("Бот запускается...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Получен сигнал остановки")
    finally:
        # Останавливаем планировщики
        await scheduler.stop_scheduler()
        await analytics_scheduler.stop_scheduler()
        
        # Закрываем сессию бота
        await bot.session.close()
        logging.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Программа прервана пользователем")