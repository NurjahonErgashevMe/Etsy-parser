"""
Тестовый скрипт для проверки экспорта в Google Sheets
Использует несколько реальных записей из top-listings.json
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

def test_sheets_export():
    print("🚀 Тестирование экспорта в Google Sheets...")
    
    tops_file = os.path.join(config.output_dir, "tops", "top-listings.json")
    if not os.path.exists(tops_file):
        print(f"❌ Файл не найден: {tops_file}")
        return
    
    # Загружаем данные
    with open(tops_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_listings = data.get("listings", {})
    if not all_listings:
        print("❌ Нет данных в top-listings.json")
        return
    
    # Берем первые 5 записей для теста
    test_listings = {}
    for i, (listing_id, listing_data) in enumerate(all_listings.items()):
        if i >= 5:
            break
        test_listings[listing_id] = listing_data
    
    print(f"📋 Выбрано {len(test_listings)} листингов для теста")
    
    # Проверяем, что у них есть daily growth
    missing_daily_growth = []
    for listing_id, listing_data in test_listings.items():
        if "views_daily_growth" not in listing_data or "likes_daily_growth" not in listing_data:
            missing_daily_growth.append(listing_id)
        else:
            print(f"✅ {listing_id}: Views/день={listing_data['views_daily_growth']}, Likes/день={listing_data['likes_daily_growth']}")
    
    if missing_daily_growth:
        print(f"⚠️ {len(missing_daily_growth)} листингов без daily growth: {missing_daily_growth}")
    else:
        print("✅ Все тестовые листинги содержат данные о дневном приросте")
    
    # Отправляем в Google Sheets (в тестовый лист)
    print("\n📊 Экспорт в Google Sheets (тестовый лист)...")
    spreadsheet_id = config.google_sheets_spreadsheet_id
    
    if not spreadsheet_id:
        print("❌ Не указан google_sheets_spreadsheet_id в конфиге")
        return
    
    sheets_service = GoogleSheetsService(config)
    
    # Используем отдельный тестовый лист
    test_sheet_name = "Test Top Listings"
    
    try:
        # Сначала проверим подключение
        if not sheets_service.test_connection(spreadsheet_id):
            print("❌ Не удалось подключиться к Google Sheets")
            return
        
        # Экспортируем данные
        print(f"\n📤 Экспорт {len(test_listings)} записей в лист '{test_sheet_name}'...")
        
        # Используем ту же функцию, но с другим именем листа
        spreadsheet = sheets_service.client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(test_sheet_name)
            print(f"✅ Лист '{test_sheet_name}' найден")
        except:
            print(f"📊 Создание нового листа '{test_sheet_name}'...")
            worksheet = spreadsheet.add_worksheet(title=test_sheet_name, rows=100, cols=10)
        
        # Очищаем лист
        worksheet.clear()
        
        # Добавляем заголовки
        worksheet.update(values=[[
            'Ссылка на товар',
            'Когда появился',
            'Когда стал хитом',
            'Просмотры (начало)',
            'Просмотры (на 60 день)',
            'Просмотры (хит/день)',
            'Лайки (начало)',
            'Лайки (на 60 день)',
            'Лайки (хит/день)',
            'Отзывы'
        ]], range_name='A1:J1')
        
        # Формируем данные
        from datetime import datetime
        rows_to_add = []
        for listing_id, listing_data in test_listings.items():
            def convert_date(date_str):
                try:
                    dt = datetime.strptime(date_str, "%d.%m.%Y_%H.%M")
                    return dt.strftime("%Y-%m-%d %H:%M")
                except:
                    return date_str
            
            views_start = int(listing_data.get('views_start', 0))
            views_hit = int(listing_data.get('views_hit', 0))
            views_daily = float(listing_data.get('views_daily_growth', 0.0))
            
            likes_start = int(listing_data.get('likes_start', 0))
            likes_hit = int(listing_data.get('likes_hit', 0))
            likes_daily = float(listing_data.get('likes_daily_growth', 0.0))
            
            reviews = int(listing_data.get('reviews', 0))
            
            rows_to_add.append([
                listing_data['url'],
                convert_date(listing_data['discovered_at']),
                convert_date(listing_data['became_hit_at']),
                views_start,
                views_hit,
                views_daily,
                likes_start,
                likes_hit,
                likes_daily,
                reviews
            ])
        
        # Записываем данные
        if rows_to_add:
            worksheet.update(values=rows_to_add, range_name='A2')
            print(f"📝 Записано {len(rows_to_add)} строк данных")
        else:
            print("⚠️ Нет данных для записи")
        
        print(f"\n✅ Тест завершен успешно!")
        print(f"📊 Проверьте лист '{test_sheet_name}' в вашей Google Таблице")
        print(f"🔍 Убедитесь, что колонки 'Просмотры (хит/день)' и 'Лайки (хит/день)' содержат числа, а не нули")
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sheets_export()
