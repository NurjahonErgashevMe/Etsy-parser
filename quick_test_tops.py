"""
Быстрый тест логики топ-хитов с имитацией данных
"""
import json
import os
from datetime import datetime, timedelta

def quick_test_tops():
    """Быстрый тест с имитацией данных"""
    
    # Создаем тестовые данные прямо в коде
    test_listing_id = "4380396448"  # Берем реальный ID из файла
    
    # Имитируем данные "вчера" и "сегодня"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y_%H.%M")
    today = datetime.now().strftime("%d.%m.%Y_%H.%M")
    
    # Создаем данные с прогрессией для топа
    test_data = {
        "listings": {
            test_listing_id: {
                yesterday: {
                    "price": "749.00",
                    "est_total_sales": 0,
                    "est_mo_sales": 0,
                    "listing_age_in_months": 1,
                    "est_reviews": 0,
                    "est_reviews_in_months": 0,
                    "conversion_rate": 0.0,
                    "views": 3,  # Начальные просмотры
                    "num_favorers": 1,  # Начальные лайки
                    "url": "https://www.etsy.com/listing/4380396448/ivory-wedding-dress-with-high-collar-a"
                },
                today: {
                    "price": "749.00",
                    "est_total_sales": 5,
                    "est_mo_sales": 5,
                    "listing_age_in_months": 1,
                    "est_reviews": 2,
                    "est_reviews_in_months": 2,
                    "conversion_rate": 0.08,
                    "views": 53,  # +50 просмотров за день = 50/день (больше 20)
                    "num_favorers": 6,  # +5 лайков за день = 5/день (больше 0.8)
                    "url": "https://www.etsy.com/listing/4380396448/ivory-wedding-dress-with-high-collar-a"
                }
            }
        }
    }
    
    # Сохраняем во временный файл
    test_file = "output/tops/test_perspective_listings.json"
    os.makedirs("output/tops", exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Тестовые данные созданы: {test_file}")
    print(f"📊 Листинг {test_listing_id}:")
    print(f"   Вчера: {test_data['listings'][test_listing_id][yesterday]['views']} просмотров, {test_data['listings'][test_listing_id][yesterday]['num_favorers']} лайков")
    print(f"   Сегодня: {test_data['listings'][test_listing_id][today]['views']} просмотров, {test_data['listings'][test_listing_id][today]['num_favorers']} лайков")
    print(f"   Прирост: +{test_data['listings'][test_listing_id][today]['views'] - test_data['listings'][test_listing_id][yesterday]['views']} просмотров/день, +{test_data['listings'][test_listing_id][today]['num_favorers'] - test_data['listings'][test_listing_id][yesterday]['num_favorers']} лайков/день")
    
    # Теперь тестируем логику
    from services.tops_service import TopsService
    
    # Временно подменяем файл
    tops_service = TopsService()
    original_file = tops_service.listings_file
    tops_service.listings_file = test_file
    
    print(f"\n🔍 Запуск оценки топ-хитов...")
    result = tops_service.evaluate_matured_listings()
    
    print(f"\n📈 РЕЗУЛЬТАТЫ:")
    print(f"🔝 Топ-хитов найдено: {len(result.get('top', {}))}")
    print(f"🗄️ В архив отправлено: {len(result.get('archived', []))}")
    
    if result.get('top'):
        print(f"\n🎉 НАЙДЕН ТОП-ХИТ!")
        for listing_id, data in result['top'].items():
            print(f"   ID: {listing_id}")
            print(f"   Просмотров/день: {data['avg_views_per_day']}")
            print(f"   Лайков/день: {data['avg_likes_per_day']}")
            print(f"   URL: {data['url']}")
    else:
        print(f"❌ Топ-хиты не найдены")
    
    # Удаляем тестовый файл
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🧹 Тестовый файл удален")

if __name__ == "__main__":
    quick_test_tops()