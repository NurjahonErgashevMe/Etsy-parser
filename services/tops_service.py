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
        self.archived_listings_file = os.path.join(self.tops_dir, "archived_listings.json")
        # Порог зрелости и метрики топа
        self.maturity_days = 60  # ~2 месяца
        self.views_threshold = 25.0  # ~25 просмотров/день
        self.likes_threshold = 1.0   # ~1 лайк/день
        self.tolerance = 0.8         # Допуск 20%
        # Колбэк-уведомитель (опционально)
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

    def _load_archived_listings(self) -> Dict:
        """Загружает архив листингов"""
        if os.path.exists(self.archived_listings_file):
            try:
                with open(self.archived_listings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки архива: {e}")
        return {"listings": {}}

    def _save_archived_listings(self, data: Dict):
        """Сохраняет архив листингов"""
        try:
            with open(self.archived_listings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Архив листингов сохранен: {self.archived_listings_file}")
        except Exception as e:
            logging.error(f"Ошибка сохранения архива: {e}")

    def set_notifier(self, notifier: Callable[[Dict], None]):
        """Устанавливает колбэк для уведомлений о топах"""
        self.notifier = notifier

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
        
        logging.info(f"Обновлено {saved_count} листингов с датой {checked_date} (пропущено как топ: {skipped_top})")
        print(f"💎 Сохранено {saved_count} перспективных листингов в tops/ (пропущено как топ: {skipped_top})")

    def evaluate_matured_listings(self) -> Dict[str, Dict]:
        """Оценивает листинги, достигшие зрелости (~2 месяца), и классифицирует их как ТОП или в Архив.
        Условия ТОП: ~25 просмотров/день и ~1 лайк/день (с допуском).
        Возвращает словарь с добавленными топами и архивированными ID.
        """
        data = self._load_existing_listings()
        all_listings = data.get("listings", {})
        if not all_listings:
            return {"top": {}, "archived": []}

        top_json = self._load_top_listings()
        archived_json = self._load_archived_listings()

        top_added: Dict[str, Dict] = {}
        archived_ids: List[str] = []
        now = datetime.now()
        to_remove: List[str] = []

        for listing_id, snapshots in all_listings.items():
            if not snapshots:
                continue
            timestamps = sorted(snapshots.keys())
            first_ts = timestamps[0]
            last_ts = timestamps[-1]
            try:
                first_dt = datetime.strptime(first_ts, "%d.%m.%Y_%H.%M")
                last_dt = datetime.strptime(last_ts, "%d.%m.%Y_%H.%M")
            except Exception:
                # Неверный формат метки времени — пропускаем
                continue

            # Проверяем зрелость (2 мес ~ 60 дней)
            if (now - first_dt).days < self.maturity_days:
                continue

            days_observed = max((last_dt - first_dt).days, 1)
            first_data = snapshots.get(first_ts, {})
            last_data = snapshots.get(last_ts, {})

            v_start = (first_data.get("views") or 0)
            v_end = (last_data.get("views") or 0)
            f_start = (first_data.get("num_favorers") or 0)
            f_end = (last_data.get("num_favorers") or 0)

            views_per_day = (v_end - v_start) / days_observed if days_observed else 0.0
            likes_per_day = (f_end - f_start) / days_observed if days_observed else 0.0

            is_top = (
                views_per_day >= self.views_threshold * self.tolerance and
                likes_per_day >= self.likes_threshold * self.tolerance
            )

            summary = {
                "listing_id": listing_id,
                "discovered_at": first_ts,
                "last_checked": last_ts,
                "url": last_data.get("url", ""),
                "days_observed": days_observed,
                "avg_views_per_day": round(views_per_day, 2),
                "avg_likes_per_day": round(likes_per_day, 2),
            }

            if is_top:
                top_json.setdefault("listings", {})
                top_json["listings"][listing_id] = summary
                top_added[listing_id] = summary
                print(
                    f"🔝 Топ-хит: {listing_id} "
                    f"({summary['avg_views_per_day']}/день, {summary['avg_likes_per_day']}/день) "
                    f"{summary['url']}"
                )
                if self.notifier:
                    try:
                        self.notifier(summary)
                    except Exception as e:
                        logging.error(f"Ошибка уведомления для топ листинга {listing_id}: {e}")
            else:
                archived_json.setdefault("listings", {})
                archived_json["listings"][listing_id] = {**summary, "reason": "below_threshold"}
                archived_ids.append(listing_id)
                print(
                    f"🗄️ Архив: {listing_id} "
                    f"({summary['avg_views_per_day']}/день, {summary['avg_likes_per_day']}/день) "
                    f"{summary['url']}"
                )

            to_remove.append(listing_id)

        # Удаляем классифицированные из перспективных и сохраняем результаты
        if to_remove:
            for lid in to_remove:
                data["listings"].pop(lid, None)
            self._save_listings(data)
            if top_added:
                self._save_top_listings(top_json)
            if archived_ids:
                self._save_archived_listings(archived_json)

        return {"top": top_added, "archived": archived_ids}
    
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
            eval_result = self.evaluate_matured_listings()
            top_count = len(eval_result.get("top", {})) if eval_result else 0
            archived_count = len(eval_result.get("archived", [])) if eval_result else 0
            if top_count or archived_count:
                print(f"🏁 Итог: в топ добавлено {top_count}, в архив {archived_count}")
            print(f"✅ Анализ завершен успешно")
        else:
            print("⚠️ Не удалось получить данные от EverBee")
            logging.warning("Не удалось получить данные от EverBee")
