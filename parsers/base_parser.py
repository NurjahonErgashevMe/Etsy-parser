"""
Базовый класс для парсеров (теперь только через браузер)
"""
from abc import ABC, abstractmethod
from typing import List
from models.product import Product

class BaseParser(ABC):
    """Базовый класс для всех парсеров"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def parse_shop_page(self, shop_url: str) -> List[Product]:
        """Парсит страницу магазина и возвращает список продуктов"""
        pass
    
    @abstractmethod
    def get_shop_name_from_url(self, url: str) -> str:
        """Извлекает название магазина из URL"""
        pass