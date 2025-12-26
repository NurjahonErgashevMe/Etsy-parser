"""
Скрипт для миграции и экспорта top-listings.json в Google Sheets
Добавляет расчет дневного прироста лайков/просмотров
"""
import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_sheets_service import GoogleSheetsService
from config.settings import config

# Setup logging
logging.basicConfig(level=logging.INFO)

def migrate_and_export():
    print("🚀 Миграция и экспорт top-listings...")
    
    tops_file = os.path.join(config.output_dir, "tops", "top-listings.json")
    if not os.path.exists(tops_file):
        print(f"❌ Файл не найден: {tops_file}")
        return
    
    # Загружаем данные
    with open(tops_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    listings = data.get("listings", {})
    if not listings:
        print("❌ Нет данных в top-listings.json")
        return
    
    print(f"📋 Найдено {len(listings)} топ-листингов")
    
    # Обновляем данные с расчетом дневного прироста
    updated_count = 0
    for listing_id, listing_data in listings.items():
        # Проверяем, есть ли уже daily growth
        if "views_daily_growth" not in listing_data or "likes_daily_growth" not in listing_data:
            views_start = listing_data.get("views_start", 0)
            views_hit = listing_data.get("views_hit", 0)
            likes_start = listing_data.get("likes_start", 0)
            likes_hit = listing_data.get("likes_hit", 0)
            days_observed = listing_data.get("days_observed", 60)
            
            # Делим на количество дней наблюдения
            divisor = days_observed if days_observed > 0 else 1
            views_daily = round((views_hit - views_start) / divisor, 2)
            likes_daily = round((likes_hit - likes_start) / divisor, 2)
            
            listing_data["views_daily_growth"] = views_daily
            listing_data["likes_daily_growth"] = likes_daily
            updated_count += 1
            
            print(f"✨ {listing_id}: Views/день={views_daily}, Likes/день={likes_daily}")
    
    if updated_count > 0:
        # Сохраняем обновленный файл
        with open(tops_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Обновлено {updated_count} листингов с расчетом дневного прироста")
    else:
        print("✅ Все листинги уже содержат данные о дневном приросте")
    
    # Отправляем в Google Sheets
    print("\n📊 Экспорт в Google Sheets...")
    spreadsheet_id = config.google_sheets_spreadsheet_id
    
    if not spreadsheet_id:
        print("❌ Не указан google_sheets_spreadsheet_id в конфиге")
        return
    
    sheets_service = GoogleSheetsService(config)
    sheets_service.add_top_listings_to_sheets(spreadsheet_id, listings)
    
    print("✅ Миграция и экспорт завершены!")

if __name__ == "__main__":
    migrate_and_export()
