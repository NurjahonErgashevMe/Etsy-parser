"""
Модели данных для продуктов
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Product:
    """Модель продукта Etsy"""
    listing_id: str
    title: str
    url: str
    shop_name: str
    price: Optional[str] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    scraped_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сохранения"""
        return {
            'listing_id': self.listing_id,
            'title': self.title,
            'url': self.url,
            'shop_name': self.shop_name,
            'price': self.price,
            'currency': self.currency,
            'image_url': self.image_url,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """Создает объект из словаря"""
        scraped_at = None
        if data.get('scraped_at'):
            scraped_at = datetime.fromisoformat(data['scraped_at'])
        
        return cls(
            listing_id=data['listing_id'],
            title=data['title'],
            url=data['url'],
            shop_name=data['shop_name'],
            price=data.get('price'),
            currency=data.get('currency'),
            image_url=data.get('image_url'),
            scraped_at=scraped_at
        )

@dataclass
class ShopComparison:
    """Результат сравнения магазина"""
    shop_name: str
    new_products: List[Product]
    removed_products: List[Product]
    total_current: int
    total_previous: int
    comparison_date: datetime
    
    def __post_init__(self):
        if self.comparison_date is None:
            self.comparison_date = datetime.now()
    
    @property
    def has_changes(self) -> bool:
        """Есть ли изменения в магазине"""
        return len(self.new_products) > 0 or len(self.removed_products) > 0
    
    def to_dict(self) -> dict:
        """Преобразует в словарь"""
        return {
            'shop_name': self.shop_name,
            'new_products': [p.to_dict() for p in self.new_products],
            'removed_products': [p.to_dict() for p in self.removed_products],
            'total_current': self.total_current,
            'total_previous': self.total_previous,
            'comparison_date': self.comparison_date.isoformat()
        }