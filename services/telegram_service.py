"""
Сервис для работы с Telegram ботом (заглушка для будущей реализации)
"""
from typing import List
from models.product import ShopComparison

class TelegramService:
    """Сервис для отправки уведомлений в Telegram"""
    
    def __init__(self, config):
        self.config = config
        self.bot_token = config.telegram_bot_token
        self.enabled = bool(self.bot_token)
    
    def send_shop_changes_notification(self, comparison: ShopComparison):
        """Отправляет уведомление об изменениях в магазине"""
        if not self.enabled:
            print("Telegram бот не настроен")
            return
        
        # TODO: Реализовать отправку уведомлений
        print(f"📱 [TELEGRAM] Уведомление об изменениях в {comparison.shop_name}")
        
        if comparison.new_products:
            print(f"   ➕ Новых товаров: {len(comparison.new_products)}")
        
        if comparison.removed_products:
            print(f"   ➖ Удаленных товаров: {len(comparison.removed_products)}")
    
    def send_monitoring_summary(self, results: List[str]):
        """Отправляет сводку по результатам мониторинга"""
        if not self.enabled:
            return
        
        # TODO: Реализовать отправку сводки
        print(f"📱 [TELEGRAM] Сводка мониторинга: обработано {len(results)} магазинов")