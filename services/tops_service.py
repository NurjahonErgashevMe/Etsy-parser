"""
Сервис для работы с топ товарами
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from utils.everbee_client import EverBeeClient


class TopsService:
    """Сервис для анализа и сохранения топ товаров"""
    
    def __init__(self, tops_dir: str = "output/tops"):
        self.tops_dir = tops_dir
        self.everbee_client = EverBeeClient()
        self.listings_file = os.path.join(self.tops_dir, "new_perspective_listings.json")
        os.makedirs(self.tops_dir, exist_ok=True)
    
    def _load_existing_listings(self) -> Dict:
        """Загружает существующие данные листингов"""
        if os.path.exists(self.listings_file):
            try:
                with open(self.listings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки существующих данных: {e}")
        
        return {"listings": {}}
    
    def _save_listings(self, data: Dict):
        """Сохраняет данные листингов"""
        try:
            with open(self.listings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Данные сохранены: {self.listings_file}")
        except Exception as e:
            logging.error(f"Ошибка сохранения данных: {e}")
    
    def analyze_new_listings(self, new_products: Dict[str, str], checked_date: str) -> Dict[str, Dict]:
        """Анализирует новые листинги через EverBee API"""
        if not new_products:
            print("Нет новых товаров для анализа")
            return {}
        
        print(f"📊 Анализ {len(new_products)} новых листингов через EverBee...")
        logging.info(f"Анализ {len(new_products)} новых листингов через EverBee...")
        
        listing_ids = list(new_products.keys())
        
        response = self.everbee_client.get_listings_batch(listing_ids)
        
        if not response or "results" not in response:
            print("❌ Не удалось получить данные от EverBee")
            logging.error("Не удалось получить данные от EverBee")
            return {}
        
        results = {}
        for listing in response.get("results", []):
            listing_id = str(listing.get("listing_id"))
            if listing_id:
                extracted_data = self.everbee_client.extract_listing_data(listing)
                results[listing_id] = extracted_data
        
        print(f"✅ Получено данных для {len(results)} листингов от EverBee")
        logging.info(f"Получено данных для {len(results)} листингов")
        return results
    
    def update_listings_data(self, new_listings_data: Dict[str, Dict], checked_date: str):
        """Обновляет данные листингов с новой датой проверки"""
        existing_data = self._load_existing_listings()
        
        for listing_id, listing_data in new_listings_data.items():
            if listing_id not in existing_data["listings"]:
                existing_data["listings"][listing_id] = {}
            
            existing_data["listings"][listing_id][checked_date] = listing_data
        
        self._save_listings(existing_data)
        
        logging.info(f"Обновлено {len(new_listings_data)} листингов с датой {checked_date}")
        print(f"💎 Сохранено {len(new_listings_data)} перспективных листингов в tops/")
    
    def process_new_products(self, new_products: Dict[str, str], checked_date: str = None):
        """Обрабатывает новые товары: анализирует и сохраняет"""
        if not new_products:
            print("Нет новых товаров для обработки")
            return
        
        if not checked_date:
            checked_date = datetime.now().strftime("%d.%m.%Y_%H.%M")
        
        print(f"\n=== АНАЛИЗ НОВЫХ ТОВАРОВ ЧЕРЕЗ EVERBEE ===")
        print(f"📅 Дата проверки: {checked_date}")
        print(f"📦 Товаров для анализа: {len(new_products)}")
        
        listings_data = self.analyze_new_listings(new_products, checked_date)
        
        if listings_data:
            self.update_listings_data(listings_data, checked_date)
            print(f"✅ Анализ завершен успешно")
        else:
            print("⚠️ Не удалось получить данные от EverBee")
            logging.warning("Не удалось получить данные от EverBee")
