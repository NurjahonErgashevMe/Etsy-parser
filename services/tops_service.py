"""
Сервис для работы с топ товарами
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable
from utils.everbee_client import EverBeeClient


class TopsService:
    """Сервис для анализа и сохранения топ товаров"""
    
    def __init__(self, tops_dir: str = "output/tops"):
        self.tops_dir = tops_dir
        self.everbee_client = EverBeeClient()
        self.listings_file = os.path.join(self.tops_dir, "new_perspective_listings.json")
        self.top_listings_file = os.path.join(self.tops_dir, "top-listings.json")
        self.notifier: Optional[Callable[[Dict], None]] = None
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

    # ===== Вспомогательные методы для топов/архива =====
    def _load_top_listings(self) -> Dict:
        """Загружает топ-листинги"""
        if os.path.exists(self.top_listings_file):
            try:
                with open(self.top_listings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки топ-листингов: {e}")
        return {"listings": {}}

    def _save_top_listings(self, data: Dict):
        """Сохраняет топ-листинги"""
        try:
            with open(self.top_listings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Топ-листинги сохранены: {self.top_listings_file}")
        except Exception as e:
            logging.error(f"Ошибка сохранения топ-листингов: {e}")



    def set_notifier(self, notifier: Callable[[Dict], None]):
        """Устанавливает колбэк для уведомлений о топах"""
        self.notifier = notifier

    def _check_listings_age(self, data: Dict, current_date: str) -> List[str]:
        """Проверяет возраст листингов и находит потенциальные топы"""
        potential_tops = []
        try:
            current_dt = datetime.strptime(current_date, "%d.%m.%Y_%H.%M")
            top_json = self._load_top_listings()
            
            for listing_id, snapshots in data.get("listings", {}).items():
                if not snapshots:
                    continue
                
                timestamps = sorted(snapshots.keys())
                first_ts = timestamps[0]
                last_ts = timestamps[-1]
                
                try:
                    first_dt = datetime.strptime(first_ts, "%d.%m.%Y_%H.%M")
                    days_diff = (current_dt.date() - first_dt.date()).days
                    
                    if days_diff > 0:
                        first_data = snapshots.get(first_ts, {})
                        last_data = snapshots.get(last_ts, {})
                        url = last_data.get("url", "")
                        
                        views_start = first_data.get("views", 0)
                        views_end = last_data.get("views", 0)
                        likes_start = first_data.get("num_favorers", 0)
                        likes_end = last_data.get("num_favorers", 0)
                        
                        views_growth = views_end - views_start
                        likes_growth = likes_end - likes_start
                        
                        logging.info(
                            f"Листинг {listing_id} отслеживается {days_diff} дн. "
                            f"(с {first_ts} до {current_date}) {url}"
                        )
                        
                        # Проверяем условия для топа: +20 просмотров и +5 лайков
                        if views_growth >= 20 and likes_growth >= 5:
                            logging.info(
                                f"🔥 ПОТЕНЦИАЛЬНЫЙ ТОП: {listing_id} | "
                                f"Просмотры: +{views_growth} | Лайки: +{likes_growth} | {url}"
                            )
                            
                            # Сохраняем в топы
                            summary = {
                                "listing_id": listing_id,
                                "url": url,
                                "discovered_at": first_ts,
                                "became_hit_at": last_ts,
                                "views_start": views_start,
                                "views_hit": views_end,
                                "likes_start": likes_start,
                                "likes_hit": likes_end,
                                "reviews": last_data.get("est_reviews", 0),
                                "days_observed": days_diff
                            }
                            
                            top_json.setdefault("listings", {})
                            top_json["listings"][listing_id] = summary
                            potential_tops.append(listing_id)
                            
                            print(
                                f"🔥 Топ-хит: {listing_id} | "
                                f"Просмотры: +{views_growth} | Лайки: +{likes_growth} | {url}"
                            )
                            
                except Exception:
                    continue
            
            # Сохраняем топы и удаляем их из перспективных
            if potential_tops:
                self._save_top_listings(top_json)
                # Удаляем топы из перспективных листингов
                for lid in potential_tops:
                    data["listings"].pop(lid, None)
                self._save_listings(data)
                
                # Отправляем топы в Google Sheets
                self._send_tops_to_sheets(top_json["listings"])
                    
        except Exception as e:
            logging.error(f"Ошибка проверки возраста листингов: {e}")
        
        return potential_tops
    
    def _send_tops_to_sheets(self, top_listings: Dict):
        """Отправляет топ-листинги в Google Sheets"""
        try:
            from config.settings import config
            from services.google_sheets_service import GoogleSheetsService
            
            spreadsheet_id = config.google_sheets_spreadsheet_id
            
            if not spreadsheet_id:
                logging.warning("Не указан google_sheets_spreadsheet_id в конфиге")
                return
            
            sheets_service = GoogleSheetsService(config)
            sheets_service.add_top_listings_to_sheets(spreadsheet_id, top_listings)
            
        except Exception as e:
            logging.error(f"Ошибка отправки топов в Google Sheets: {e}")
    
    def format_top_hit_message(self, summary: Dict) -> str:
        """Форматирует сообщение о топ-хите"""
        return f"""🔥 <b>НАЙДЕН ТОП-ХИТ!</b>

🔗 <b>Ссылка:</b> <a href='{summary['url']}'>Открыть на Etsy</a>

📅 <b>Когда появился:</b> {summary['discovered_at']}
🎆 <b>Когда стал хитом:</b> {summary['became_hit_at']}

👀 <b>Просмотры:</b> {summary['views_start']} → {summary['views_hit']} (+{summary['views_hit'] - summary['views_start']})
❤️ <b>Лайки:</b> {summary['likes_start']} → {summary['likes_hit']} (+{summary['likes_hit'] - summary['likes_start']})
⭐ <b>Отзывы:</b> {summary['reviews']}

📈 <b>Дней наблюдения:</b> {summary['days_observed']}"""
        
        return potential_tops

    def cleanup_perspective_from_tops(self) -> int:
        """Удаляет из new_perspective_listings.json листинги, которые уже есть в топах.
        Возвращает количество удаленных.
        """
        data = self._load_existing_listings()
        tops = self._load_top_listings()
        perspective = data.get("listings", {})
        top_ids = set(tops.get("listings", {}).keys())
        if not perspective or not top_ids:
            return 0
        removed = 0
        for lid in list(perspective.keys()):
            if lid in top_ids:
                perspective.pop(lid, None)
                removed += 1
        if removed:
            data["listings"] = perspective
            self._save_listings(data)
            logging.info(f"Очистка перспективных: удалено {removed} уже-топ листингов")
            print(f"🧹 Очистка: удалено {removed} листингов, уже попавших в топ")
        return removed
    
    def analyze_new_listings(self, new_products: Dict[str, str], checked_date: str) -> Dict[str, Dict]:
        """Анализирует новые листинги через EverBee API"""
        if not new_products:
            print("Нет новых товаров для анализа")
            return {}
        
        print(f"📊 Анализ {len(new_products)} новых листингов через EverBee...")
        logging.info(f"Анализ {len(new_products)} новых листингов через EverBee...")
        
        # Исключаем уже зафиксированные топ-листинги из анализа
        top_existing = set(self._load_top_listings().get("listings", {}).keys())
        listing_ids = [lid for lid in new_products.keys() if lid not in top_existing]
        
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
        top_ids = set(self._load_top_listings().get("listings", {}).keys())

        saved_count = 0
        skipped_top = 0
        
        for listing_id, listing_data in new_listings_data.items():
            # Пропускаем уже попавшие в топ
            if listing_id in top_ids:
                skipped_top += 1
                continue
            if listing_id not in existing_data["listings"]:
                existing_data["listings"][listing_id] = {}
            existing_data["listings"][listing_id][checked_date] = listing_data
            saved_count += 1
        
        self._save_listings(existing_data)
        
        # Проверяем листинги старше 1 дня и находим топы
        potential_tops = self._check_listings_age(existing_data, checked_date)
        
        # Удаляем новые топы из перспективных
        if potential_tops:
            for lid in potential_tops:
                existing_data["listings"].pop(lid, None)
            self._save_listings(existing_data)
        
        logging.info(f"Обновлено {saved_count} листингов с датой {checked_date} (пропущено как топ: {skipped_top})")
        print(f"💎 Сохранено {saved_count} перспективных листингов в tops/ (пропущено как топ: {skipped_top})")
        
        if potential_tops:
            print(f"🔥 Найдено {len(potential_tops)} потенциальных топ-хитов!")


    
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

        # Очистка перспективных от уже-топовых записей
        self.cleanup_perspective_from_tops()
        
        listings_data = self.analyze_new_listings(new_products, checked_date)
        
        if listings_data:
            self.update_listings_data(listings_data, checked_date)
            print(f"✅ Анализ завершен успешно")
        else:
            print("⚠️ Не удалось получить данные от EverBee")
            logging.warning("Не удалось получить данные от EverBee")
