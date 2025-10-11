"""
Сервис для аналитики изменений листингов
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from utils.everbee_client import EverBeeClient


class AnalyticsService:
    """Сервис для отслеживания изменений в статистике листингов"""
    
    def __init__(self, tops_dir: str = "output/tops"):
        self.tops_dir = tops_dir
        self.everbee_client = EverBeeClient()
        self.listings_file = os.path.join(self.tops_dir, "new_perspective_listings.json")
        os.makedirs(self.tops_dir, exist_ok=True)
    
    def _load_listings_data(self) -> Dict:
        """Загружает данные листингов"""
        if os.path.exists(self.listings_file):
            try:
                with open(self.listings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки данных листингов: {e}")
        
        return {"listings": {}}
    
    def _save_listings_data(self, data: Dict):
        """Сохраняет данные листингов"""
        try:
            with open(self.listings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Данные аналитики сохранены: {self.listings_file}")
        except Exception as e:
            logging.error(f"Ошибка сохранения данных аналитики: {e}")
    
    def get_all_listing_ids(self) -> List[str]:
        """Получает все ID листингов из базы"""
        data = self._load_listings_data()
        listing_ids = list(data.get("listings", {}).keys())
        logging.info(f"Найдено {len(listing_ids)} листингов для аналитики")
        return listing_ids
    
    def fetch_current_stats(self, listing_ids: List[str]) -> Dict[str, Dict]:
        """Получает текущую статистику листингов через EverBee API пакетами по 64"""
        if not listing_ids:
            logging.warning("Нет листингов для получения статистики")
            return {}
        
        logging.info(f"Запрос статистики для {len(listing_ids)} листингов...")
        
        results = {}
        batch_size = 64
        
        # Разбиваем на пакеты по 64 листинга
        for i in range(0, len(listing_ids), batch_size):
            batch = listing_ids[i:i + batch_size]
            logging.info(f"Обработка пакета {i//batch_size + 1}: {len(batch)} листингов")
            
            response = self.everbee_client.get_listings_batch(batch)
            
            if response and "results" in response:
                for listing in response.get("results", []):
                    listing_id = str(listing.get("listing_id"))
                    if listing_id:
                        extracted_data = self.everbee_client.extract_listing_data(listing)
                        results[listing_id] = extracted_data
            else:
                logging.error(f"Не удалось получить данные для пакета {i//batch_size + 1}")
        
        logging.info(f"Получена статистика для {len(results)} листингов")
        return results
    
    def save_analytics_snapshot(self, stats: Dict[str, Dict], timestamp: str):
        """Сохраняет снимок статистики с временной меткой и удаляет предыдущие снимки без изменений"""
        data = self._load_listings_data()
        removed_count = 0
        
        for listing_id, listing_stats in stats.items():
            if listing_id not in data["listings"]:
                data["listings"][listing_id] = {}
            
            # Получаем список всех снимков для этого листинга
            timestamps = sorted(data["listings"][listing_id].keys())
            
            # Если есть предыдущие снимки, проверяем на изменения
            if len(timestamps) >= 1:
                last_timestamp = timestamps[-1]
                last_stats = data["listings"][listing_id][last_timestamp]
                
                # Проверяем, есть ли изменения
                has_changes = False
                for key in ["est_total_sales", "est_mo_sales", "est_reviews", "est_reviews_in_months", "views", "num_favorers", "conversion_rate"]:
                    if last_stats.get(key) != listing_stats.get(key):
                        has_changes = True
                        break
                
                # Если нет изменений, удаляем предыдущий снимок (кроме первого)
                if not has_changes and len(timestamps) > 1 and last_timestamp != timestamps[0]:
                    del data["listings"][listing_id][last_timestamp]
                    removed_count += 1
            
            # Добавляем новый снимок
            data["listings"][listing_id][timestamp] = listing_stats
        
        self._save_listings_data(data)
        logging.info(f"Сохранен снимок аналитики для {len(stats)} листингов с меткой {timestamp} (удалено {removed_count} дубликатов)")
    
    def calculate_changes(self, listing_id: str, old_timestamp: str, new_timestamp: str) -> Dict:
        """Вычисляет изменения между двумя снимками статистики"""
        data = self._load_listings_data()
        
        if listing_id not in data["listings"]:
            return {}
        
        listing_data = data["listings"][listing_id]
        
        if old_timestamp not in listing_data or new_timestamp not in listing_data:
            return {}
        
        old_stats = listing_data[old_timestamp]
        new_stats = listing_data[new_timestamp]
        
        changes = {}
        
        numeric_fields = [
            "est_total_sales", "est_mo_sales", "listing_age_in_months",
            "est_reviews", "est_reviews_in_months", "views", "num_favorers"
        ]
        
        for field in numeric_fields:
            old_val = old_stats.get(field, 0)
            new_val = new_stats.get(field, 0)
            
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                diff = new_val - old_val
                if diff != 0:
                    changes[field] = {
                        "old": old_val,
                        "new": new_val,
                        "diff": diff
                    }
        
        if old_stats.get("conversion_rate") != new_stats.get("conversion_rate"):
            changes["conversion_rate"] = {
                "old": old_stats.get("conversion_rate", 0),
                "new": new_stats.get("conversion_rate", 0),
                "diff": round(new_stats.get("conversion_rate", 0) - old_stats.get("conversion_rate", 0), 2)
            }
        
        return changes
    
    def get_all_timestamps_for_listing(self, listing_id: str) -> List[str]:
        """Получает все временные метки для листинга"""
        data = self._load_listings_data()
        
        if listing_id not in data["listings"]:
            return []
        
        timestamps = list(data["listings"][listing_id].keys())
        timestamps.sort()
        return timestamps
    
    def run_analytics(self) -> Tuple[str, Dict[str, Dict]]:
        """Запускает процесс аналитики: получает текущую статистику и сохраняет"""
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M")
        
        listing_ids = self.get_all_listing_ids()
        
        if not listing_ids:
            logging.warning("Нет листингов для аналитики")
            return timestamp, {}
        
        current_stats = self.fetch_current_stats(listing_ids)
        
        if current_stats:
            self.save_analytics_snapshot(current_stats, timestamp)
        
        return timestamp, current_stats
    
    def generate_changes_report(self) -> List[Dict]:
        """Генерирует отчет об изменениях для всех листингов (сравнение с первым снимком)"""
        data = self._load_listings_data()
        report = []
        
        for listing_id, timestamps_data in data["listings"].items():
            timestamps = sorted(timestamps_data.keys())
            
            if len(timestamps) < 2:
                continue
            
            first_timestamp = timestamps[0]
            latest_timestamp = timestamps[-1]
            
            changes = self.calculate_changes(listing_id, first_timestamp, latest_timestamp)
            
            if changes:
                report.append({
                    "listing_id": listing_id,
                    "old_timestamp": first_timestamp,
                    "new_timestamp": latest_timestamp,
                    "changes": changes,
                    "url": timestamps_data[latest_timestamp].get("url", "")
                })
        
        return report
    
    def format_change_value(self, value: float) -> str:
        """Форматирует значение изменения с знаком"""
        if value > 0:
            return f"+{value}"
        return str(value)
    
    def format_changes_message(self, report: List[Dict]) -> str:
        """Форматирует отчет об изменениях в читаемое сообщение"""
        if not report:
            return "📊 Нет изменений в статистике листингов"
        
        field_names = {
            "views": "Просмотры",
            "num_favorers": "Лайки",
            "est_total_sales": "Всего продаж",
            "est_mo_sales": "Продаж в месяц",
            "est_reviews": "Отзывы",
            "est_reviews_in_months": "Отзывов в месяц",
            "conversion_rate": "Конверсия",
            "listing_age_in_months": "Возраст (мес)"
        }
        
        messages = []
        messages.append("📊 <b>ОТЧЕТ ОБ ИЗМЕНЕНИЯХ В СТАТИСТИКЕ</b>\n")
        
        for item in report:
            listing_id = item["listing_id"]
            old_ts = item["old_timestamp"]
            new_ts = item["new_timestamp"]
            changes = item["changes"]
            url = item["url"]
            
            msg = f"\n🔹 <b>Листинг {listing_id}</b>\n"
            msg += f"📅 {old_ts} → {new_ts}\n"
            
            if url:
                msg += f"🔗 <a href='{url}'>Открыть на Etsy</a>\n"
            
            msg += "\n<b>Изменения:</b>\n"
            
            for field, change_data in changes.items():
                field_name = field_names.get(field, field)
                diff = change_data["diff"]
                
                if field == "conversion_rate":
                    msg += f"• {field_name}: {self.format_change_value(diff)}\n"
                else:
                    msg += f"• {field_name}: {self.format_change_value(diff)}\n"
            
            messages.append(msg)
        
        return "\n".join(messages)
