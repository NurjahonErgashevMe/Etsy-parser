"""
Сервис для работы с данными
Структура: output/parsing/ (новинки), output/tops/ (топ товары)
"""
import os
import pandas as pd
import glob
import json
import shutil
import logging
from datetime import datetime
from typing import List, Optional, Dict
from models.product import Product, ShopComparison

class DataService:
    """Сервис для сохранения и загрузки данных"""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = config.output_dir
        
        self.parsing_dir = os.path.join(self.output_dir, "parsing")
        self.tops_dir = os.path.join(self.output_dir, "tops")
        
        self.current_parsing_folder = None
        self.current_parsing_dir = None
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.parsing_dir, exist_ok=True)
        os.makedirs(self.tops_dir, exist_ok=True)
        
        logging.info(f"📁 Структура: parsing={self.parsing_dir}, tops={self.tops_dir}")
    
    def start_parsing_session(self) -> str:
        """Создаёт папку для текущего сеанса парсинга"""
        self.current_parsing_folder = datetime.now().strftime("%d.%m.%Y_%H.%M")
        self.current_parsing_dir = os.path.join(self.parsing_dir, self.current_parsing_folder)
        os.makedirs(self.current_parsing_dir, exist_ok=True)
        
        print(f"📁 Создана папка: parsing/{self.current_parsing_folder}")
        return self.current_parsing_dir
    
    def save_products_to_excel(self, products: List[Product], shop_name: str) -> str:
        """Сохраняет продукты в Excel файл"""
        if not products:
            print("Нет данных для сохранения")
            return None
        
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        filename = os.path.join(self.current_parsing_dir, f"{shop_name}.xlsx")
        data = [product.to_dict() for product in products]
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        
        print(f"Данные сохранены: {filename}")
        return filename
    
    def load_products_from_excel(self, filename: str) -> List[Product]:
        """Загружает продукты из Excel файла"""
        try:
            df = pd.read_excel(filename)
            products = []
            
            for _, row in df.iterrows():
                product = Product.from_dict(row.to_dict())
                products.append(product)
            
            return products
            
        except Exception as e:
            print(f"Ошибка при загрузке файла {filename}: {e}")
            return []
    
    def get_latest_file_for_shop(self, shop_name: str) -> Optional[str]:
        """Возвращает путь к последнему файлу для магазина"""
        pattern = f"{self.parsing_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        if not files:
            old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
            files = glob.glob(old_pattern)
            
            legacy_pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
            legacy_files = glob.glob(legacy_pattern)
            legacy_files = [f for f in legacy_files if not any(x in f for x in ["/parsing/", "/tops/", "\\parsing\\", "\\tops\\"])]
            files.extend(legacy_files)
        
        if not files:
            return None
        
        files.sort(key=os.path.getctime, reverse=True)
        return files[0]
    
    def get_previous_file_for_shop(self, shop_name: str) -> Optional[str]:
        """Возвращает путь к предпоследнему файлу для магазина"""
        pattern = f"{self.parsing_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
        files.extend(glob.glob(old_pattern))
        
        legacy_pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
        legacy_files = glob.glob(legacy_pattern)
        legacy_files = [f for f in legacy_files if not any(x in f for x in ["/parsing/", "/tops/", "\\parsing\\", "\\tops\\"])]
        files.extend(legacy_files)
        
        if len(files) < 2:
            return None
        
        files.sort(key=os.path.getctime, reverse=True)
        return files[1]
    
    def get_all_files_for_shop(self, shop_name: str) -> List[str]:
        """Возвращает все файлы для магазина"""
        pattern = f"{self.parsing_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
        files.extend(glob.glob(old_pattern))
        
        legacy_pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
        legacy_files = glob.glob(legacy_pattern)
        legacy_files = [f for f in legacy_files if not any(x in f for x in ["/parsing/", "/tops/", "\\parsing\\", "\\tops\\"])]
        files.extend(legacy_files)
        
        files.sort(key=os.path.getctime, reverse=True)
        return files
    
    def compare_shop_data(self, current_products: List[Product], shop_name: str) -> Optional[ShopComparison]:
        """Сравнивает текущие данные с предыдущими"""
        previous_file = self.get_previous_file_for_shop(shop_name)
        
        if not previous_file:
            print(f"Нет предыдущих данных для сравнения магазина {shop_name}")
            return None
        
        previous_products = self.load_products_from_excel(previous_file)
        
        if not previous_products:
            print(f"Не удалось загрузить предыдущие данные для {shop_name}")
            return None
        
        current_ids = {p.listing_id for p in current_products}
        previous_ids = {p.listing_id for p in previous_products}
        
        new_ids = current_ids - previous_ids
        removed_ids = previous_ids - current_ids
        
        new_products = [p for p in current_products if p.listing_id in new_ids]
        removed_products = [p for p in previous_products if p.listing_id in removed_ids]
        
        comparison = ShopComparison(
            shop_name=shop_name,
            new_products=new_products,
            removed_products=removed_products,
            total_current=len(current_products),
            total_previous=len(previous_products),
            comparison_date=datetime.now()
        )
        
        return comparison
    
    def print_comparison_results(self, comparison: ShopComparison):
        """Выводит результаты сравнения в консоль"""
        print(f"\n=== СРАВНЕНИЕ ДЛЯ {comparison.shop_name} ===")
        print(f"Текущих товаров: {comparison.total_current}")
        print(f"Предыдущих товаров: {comparison.total_previous}")
        print(f"Новых товаров: {len(comparison.new_products)}")
        print(f"Удаленных товаров: {len(comparison.removed_products)}")
        
        if comparison.new_products:
            print("\nНовые товары:")
            for product in comparison.new_products:
                print(f"  - {product.title} (ID: {product.listing_id})")
        
        if comparison.removed_products:
            print("\nУдаленные товары:")
            for product in comparison.removed_products:
                print(f"  - {product.title} (ID: {product.listing_id})")
        
        if not comparison.has_changes:
            print("Изменений не обнаружено")
    
    def save_results_to_json(self, all_shop_products: Dict[str, List[Product]]) -> str:
        """Сохраняет результаты в results.json"""
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        results_file = os.path.join(self.current_parsing_dir, "results.json")
        
        shops_data = {}
        for shop_name, products in all_shop_products.items():
            shops_data[shop_name] = {product.listing_id: product.url for product in products}
        
        results = {"shops": shops_data}
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Результаты сохранены: {results_file}")
        return results_file
    
    def load_results_from_json(self, results_file: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Загружает результаты из results.json"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("shops", {})
        except Exception as e:
            print(f"Ошибка при загрузке файла {results_file}: {e}")
            return None
    
    def get_previous_results_file(self) -> Optional[str]:
        """Находит последний файл results.json"""
        current_folder_name = self.current_parsing_folder if self.current_parsing_folder else datetime.now().strftime("%d.%m.%Y_%H.%M")
        date_folders = []
        
        if os.path.exists(self.parsing_dir):
            for item in os.listdir(self.parsing_dir):
                item_path = os.path.join(self.parsing_dir, item)
                if os.path.isdir(item_path) and item != current_folder_name:
                    results_file = os.path.join(item_path, "results.json")
                    if os.path.exists(results_file):
                        try:
                            folder_datetime = datetime.strptime(item, "%d.%m.%Y_%H.%M") if "_" in item else datetime.strptime(item, "%d.%m.%Y")
                            date_folders.append((folder_datetime, results_file))
                        except ValueError:
                            continue
        
        if os.path.exists(self.output_dir):
            for item in os.listdir(self.output_dir):
                if item in ["parsing", "tops"]:
                    continue
                    
                item_path = os.path.join(self.output_dir, item)
                if os.path.isdir(item_path) and item != current_folder_name:
                    results_file = os.path.join(item_path, "results.json")
                    if os.path.exists(results_file):
                        try:
                            folder_datetime = datetime.strptime(item, "%d.%m.%Y_%H.%M") if "_" in item else datetime.strptime(item, "%d.%m.%Y")
                            date_folders.append((folder_datetime, results_file))
                        except ValueError:
                            continue
        
        if not date_folders:
            return None
        
        date_folders.sort(key=lambda x: x[0], reverse=True)
        return date_folders[0][1]
    
    def compare_all_shops_results(self, current_results: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """Сравнивает текущие результаты с предыдущими и находит новые товары"""
        previous_results_file = self.get_previous_results_file()
        
        if not previous_results_file:
            print("Нет предыдущих результатов для сравнения - все товары считаются новыми")
            new_products = {}
            for shop_name, shop_products in current_results.items():
                new_products.update(shop_products)
            return new_products
        
        previous_results = self.load_results_from_json(previous_results_file)
        
        if not previous_results:
            print("Не удалось загрузить предыдущие результаты - все товары считаются новыми")
            new_products = {}
            for shop_name, shop_products in current_results.items():
                new_products.update(shop_products)
            return new_products
        
        new_products = {}
        
        # print(f"Сравниваем магазины:")
        # print(f"  Текущие магазины: {list(current_results.keys())}")
        # print(f"  Предыдущие магазины: {list(previous_results.keys())}")
        
        for shop_name in current_results:
            if shop_name in previous_results:
                current_listings = set(current_results[shop_name].keys())
                previous_listings = set(previous_results[shop_name].keys())
                
                print(f"  Магазин {shop_name}:")
                print(f"    Текущие товары: {len(current_listings)}")
                print(f"    Предыдущие товары: {len(previous_listings)}")
                
                new_listing_ids = current_listings - previous_listings
                
                if new_listing_ids:
                    print(f"    Новые товары: {list(new_listing_ids)}")
                    for listing_id in new_listing_ids:
                        new_products[listing_id] = current_results[shop_name][listing_id]
                    print(f"Магазин {shop_name}: найдено {len(new_listing_ids)} новых товаров")
                else:
                    print(f"    Новых товаров не найдено")
            else:
                print(f"Магазин {shop_name}: новый магазин, пропускаем сравнение")
        
        print(f"Всего найдено новых товаров: {len(new_products)}")
        # if new_products:
        #     print("Список новых товаров:")
        #     for listing_id, url in new_products.items():
        #         print(f"  - {listing_id}: {url}")

        
        return new_products
    
    def save_results_with_new_products(self, all_shop_products: Dict[str, List[Product]], new_products: Dict[str, str], new_products_full_data: Dict[str, Product] = None) -> str:
        """Сохраняет результаты с новыми товарами"""
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        results_file = os.path.join(self.current_parsing_dir, "results.json")
        
        shops_data = {}
        for shop_name, products in all_shop_products.items():
            shops_data[shop_name] = {product.listing_id: product.url for product in products}
        
        results = {
            "shops": shops_data,
            "new_products": new_products
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Результаты с новыми товарами сохранены: {results_file}")
        self.save_new_products_to_sheets(new_products, results)
        
        # Сохраняем новые товары в new_perspective_listings.json
        if new_products:
            self.save_new_perspective_listings(new_products, new_products_full_data)
        
        return results_file
    
    def save_new_perspective_listings(self, new_products: Dict[str, str], new_products_full_data: Dict[str, Product] = None):
        """Сохраняет новые товары в new_perspective_listings.json с полными данными из EverBee"""
        from utils.everbee_client import EverBeeClient
        
        new_listings_file = os.path.join(self.tops_dir, "new_perspective_listings.json")
        
        # Загружаем существующие данные
        existing_data = {"listings": {}}
        if os.path.exists(new_listings_file):
            try:
                with open(new_listings_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки {new_listings_file}: {e}")
        
        # Получаем данные из EverBee пакетным запросом
        everbee_client = EverBeeClient()
        current_session = self.current_parsing_folder or datetime.now().strftime("%d.%m.%Y_%H.%M")
        
        # Получаем все данные одним запросом
        listing_ids = list(new_products.keys())
        everbee_data_batch = {}
        
        try:
            if listing_ids:
                batch_data = everbee_client.get_listings_batch(listing_ids)
                if batch_data and 'results' in batch_data:
                    for listing_info in batch_data['results']:
                        listing_id = str(listing_info.get('listing_id', ''))
                        everbee_data_batch[listing_id] = everbee_client.extract_listing_data(listing_info)
        except Exception as e:
            logging.error(f"Ошибка получения пакетных данных EverBee: {e}")
        
        # Добавляем данные в структуру
        for listing_id, url in new_products.items():
            if listing_id not in existing_data["listings"]:
                existing_data["listings"][listing_id] = {}
            
            # Используем данные из пакетного запроса или только URL
            everbee_data = everbee_data_batch.get(listing_id, {"url": url})
            existing_data["listings"][listing_id][current_session] = everbee_data
        
        # Сохраняем обновленные данные
        with open(new_listings_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Новые листинги с EverBee данными сохранены в {new_listings_file}: {len(new_products)} товаров")
    
    def save_new_products_to_sheets(self, new_products: Dict[str, str], results: Dict = None):
        """Сохраняет новые товары в Google Sheets"""
        if not new_products:
            return
        
        if hasattr(self.config, 'google_sheets_enabled') and self.config.google_sheets_enabled:
            try:
                from services.google_sheets_service import GoogleSheetsService
                sheets_service = GoogleSheetsService(self.config)
                
                if sheets_service.enabled:
                    sheets_service.add_new_products_to_sheets(
                        self.config.google_sheets_spreadsheet_id,
                        new_products,
                        "Etsy Products",
                        results
                    )
            except Exception as e:
                print(f"⚠️ Ошибка Google Sheets: {e}")
    
    def cleanup_output_folder(self) -> bool:
        """Очищает папку parsing/, оставляя только текущую. Папка tops/ не трогается."""
        if not self.current_parsing_folder:
            return True
        
        try:
            folders_to_delete = []
            
            if os.path.exists(self.parsing_dir):
                for item in os.listdir(self.parsing_dir):
                    item_path = os.path.join(self.parsing_dir, item)
                    if os.path.isdir(item_path) and item != self.current_parsing_folder:
                        folders_to_delete.append(item_path)
            
            if os.path.exists(self.output_dir):
                for item in os.listdir(self.output_dir):
                    if item in ["parsing", "tops"]:
                        continue
                    
                    item_path = os.path.join(self.output_dir, item)
                    if os.path.isdir(item_path):
                        folders_to_delete.append(item_path)
            
            if not folders_to_delete:
                return True
            
            deleted_count = 0
            for folder_path in folders_to_delete:
                try:
                    shutil.rmtree(folder_path, ignore_errors=True)
                    if not os.path.exists(folder_path):
                        deleted_count += 1
                except Exception as e:
                    logging.error(f"Ошибка удаления {folder_path}: {e}")
            
            logging.info(f"Очистка parsing/: удалено {deleted_count}/{len(folders_to_delete)} папок")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка очистки: {e}")
            return False
    
    def load_shop_urls(self) -> List[str]:
        """Загружает список URL магазинов из Google Sheets"""
        if hasattr(self.config, 'google_sheets_enabled') and self.config.google_sheets_enabled:
            try:
                from services.google_sheets_service import GoogleSheetsService
                sheets_service = GoogleSheetsService(self.config)
                
                if sheets_service.enabled:
                    urls = sheets_service.load_shop_urls_from_sheets(
                        self.config.google_sheets_spreadsheet_id,
                        "Etsy Shops"
                    )
                    if urls:
                        print(f"📊 Загружено {len(urls)} URL из Google Sheets")
                        return urls
            except Exception as e:
                print(f"⚠️ Ошибка Google Sheets: {e}")
        
        return []
