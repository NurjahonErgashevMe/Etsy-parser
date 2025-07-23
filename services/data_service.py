"""
Сервис для работы с данными
"""
import os
import pandas as pd
import glob
import json
import shutil
import random
import string
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from models.product import Product, ShopComparison

class DataService:
    """Сервис для сохранения и загрузки данных"""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = config.output_dir
        self.current_parsing_folder = None  # Папка для текущего сеанса парсинга
        self.current_parsing_dir = None     # Полный путь к папке текущего сеанса
        os.makedirs(self.output_dir, exist_ok=True)
    
    def start_parsing_session(self) -> str:
        """Создаёт папку для текущего сеанса парсинга и возвращает её путь"""
        self.current_parsing_folder = datetime.now().strftime("%d.%m.%Y_%H.%M")
        self.current_parsing_dir = os.path.join(self.output_dir, self.current_parsing_folder)
        os.makedirs(self.current_parsing_dir, exist_ok=True)
        
        print(f"📁 Создана папка для сеанса парсинга: {self.current_parsing_folder}")
        return self.current_parsing_dir
    
    def save_products_to_excel(self, products: List[Product], shop_name: str) -> str:
        """Сохраняет продукты в Excel файл в папку текущего сеанса парсинга"""
        if not products:
            print("Нет данных для сохранения")
            return None
        
        # Используем папку текущего сеанса парсинга или создаём новую
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        # Формируем имя файла
        filename = os.path.join(self.current_parsing_dir, f"{shop_name}.xlsx")
        
        # Преобразуем продукты в DataFrame
        data = [product.to_dict() for product in products]
        df = pd.DataFrame(data)
        
        # Сохраняем в Excel
        df.to_excel(filename, index=False)
        
        print(f"Данные сохранены в файл: {filename}")
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
        """Возвращает путь к последнему файлу для магазина в новом формате"""
        # Ищем файлы в папках с датами
        pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        if not files:
            # Проверяем старый формат для обратной совместимости
            old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
            files = glob.glob(old_pattern)
        
        if not files:
            return None
        
        # Сортируем по времени создания
        files.sort(key=os.path.getctime, reverse=True)
        return files[0]
    
    def get_previous_file_for_shop(self, shop_name: str) -> Optional[str]:
        """Возвращает путь к предпоследнему файлу для магазина"""
        # Ищем файлы в папках с датами
        pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        # Добавляем файлы в старом формате для обратной совместимости
        old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
        old_files = glob.glob(old_pattern)
        files.extend(old_files)
        
        if len(files) < 2:
            return None
        
        # Сортируем по времени создания
        files.sort(key=os.path.getctime, reverse=True)
        return files[1]
    
    def get_all_files_for_shop(self, shop_name: str) -> List[str]:
        """Возвращает все файлы для магазина, отсортированные по дате"""
        # Ищем файлы в новом формате
        pattern = f"{self.output_dir}/*/{shop_name}.xlsx"
        files = glob.glob(pattern)
        
        # Добавляем файлы в старом формате
        old_pattern = f"{self.output_dir}/{shop_name}_*.xlsx"
        old_files = glob.glob(old_pattern)
        files.extend(old_files)
        
        # Сортируем по времени создания
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
        
        # Создаем множества ID для сравнения
        current_ids = {p.listing_id for p in current_products}
        previous_ids = {p.listing_id for p in previous_products}
        
        # Находим новые и удаленные товары
        new_ids = current_ids - previous_ids
        removed_ids = previous_ids - current_ids
        
        # Создаем списки продуктов
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
        """Сохраняет результаты всех магазинов в results.json в папку текущего сеанса парсинга"""
        # Используем папку текущего сеанса парсинга или создаём новую
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        results_file = os.path.join(self.current_parsing_dir, "results.json")
        
        # Формируем структуру данных: {shops: {"shop_name": {"listing-id": "url", ...}, ...}}
        shops_data = {}
        for shop_name, products in all_shop_products.items():
            shops_data[shop_name] = {product.listing_id: product.url for product in products}
        
        results = {"shops": shops_data}
        
        # Сохраняем в JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Результаты сохранены в файл: {results_file}")
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
        """Находит самый последний файл results.json до текущего времени"""
        # Исключаем текущую папку парсинга из поиска
        current_folder_name = self.current_parsing_folder if self.current_parsing_folder else datetime.now().strftime("%d.%m.%Y_%H.%M")
        
        # Получаем все папки с датами
        date_folders = []
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)
            if os.path.isdir(item_path) and item != current_folder_name:
                # Проверяем, есть ли в папке results.json
                results_file = os.path.join(item_path, "results.json")
                if os.path.exists(results_file):
                    try:
                        # Парсим дату и время из названия папки
                        if "_" in item:
                            # Новый формат DD.MM.YYYY_HH.MM
                            folder_datetime = datetime.strptime(item, "%d.%m.%Y_%H.%M")
                        else:
                            # Старый формат DD.MM.YYYY (для обратной совместимости)
                            folder_datetime = datetime.strptime(item, "%d.%m.%Y")
                        date_folders.append((folder_datetime, results_file))
                    except ValueError:
                        continue
        
        if not date_folders:
            print("Предыдущие результаты не найдены")
            return None
        
        # Сортируем по дате и берем самый последний
        date_folders.sort(key=lambda x: x[0], reverse=True)
        latest_file = date_folders[0][1]
        
        print(f"Найден предыдущий файл результатов: {latest_file}")
        return latest_file
    
    def compare_all_shops_results(self, current_results: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """Сравнивает текущие результаты с предыдущими и находит новые товары"""
        previous_results_file = self.get_previous_results_file()
        
        if not previous_results_file:
            print("Нет предыдущих результатов для сравнения")
            return {}
        
        previous_results = self.load_results_from_json(previous_results_file)
        
        if not previous_results:
            print("Не удалось загрузить предыдущие результаты")
            return {}
        
        new_products = {}
        
        print(f"Сравниваем магазины:")
        print(f"  Текущие магазины: {list(current_results.keys())}")
        print(f"  Предыдущие магазины: {list(previous_results.keys())}")
        
        # Сравниваем только те магазины, которые были в предыдущих результатах
        for shop_name in current_results:
            if shop_name in previous_results:
                current_listings = set(current_results[shop_name].keys())
                previous_listings = set(previous_results[shop_name].keys())
                
                print(f"  Магазин {shop_name}:")
                print(f"    Текущие товары: {len(current_listings)}")
                print(f"    Предыдущие товары: {len(previous_listings)}")
                
                # Находим новые listing-id
                new_listing_ids = current_listings - previous_listings
                
                if new_listing_ids:
                    print(f"    Новые товары: {list(new_listing_ids)}")
                    # Добавляем новые товары в результат
                    for listing_id in new_listing_ids:
                        new_products[listing_id] = current_results[shop_name][listing_id]
                    print(f"Магазин {shop_name}: найдено {len(new_listing_ids)} новых товаров")
                else:
                    print(f"    Новых товаров не найдено")
            else:
                print(f"Магазин {shop_name}: новый магазин, пропускаем сравнение")
        
        print(f"Всего найдено новых товаров: {len(new_products)}")
        if new_products:
            print("Список новых товаров:")
            for listing_id, url in new_products.items():
                print(f"  - {listing_id}: {url}")
        
        return new_products
    
    def generate_mock_products(self) -> Dict[str, str]:
        """Выбирает случайные товары из статического набора моковых данных для магазина MockShop"""

        # Статический набор моковых товаров
        static_mock_products = {
            "1234567890": "https://www.etsy.com/listing/1234567890/handmade-ceramic-mug",
            "2345678901": "https://www.etsy.com/listing/2345678901/vintage-leather-wallet",
            "3456789012": "https://www.etsy.com/listing/3456789012/wooden-cutting-board",
            "4567890123": "https://www.etsy.com/listing/4567890123/silver-pendant-necklace",
            "5678901234": "https://www.etsy.com/listing/5678901234/cotton-tote-bag",
            "6789012345": "https://www.etsy.com/listing/6789012345/scented-soy-candle"
        }
        
        # Выбираем случайное количество товаров от 3 до 6
        num_products = random.randint(3, 6)
        
        # Случайно выбираем товары из статического набора
        selected_items = random.sample(list(static_mock_products.items()), num_products)
        mock_products = dict(selected_items)
        
        print(f"Выбрано {num_products} товаров из статического набора для магазина MockShop")
        return mock_products
    
    def add_mock_shop_to_results(self, all_shop_products: Dict[str, List[Product]]) -> Dict[str, List[Product]]:
        """Добавляет моковый магазин MockShop к результатам ДО сравнения"""
        # Генерируем моковые товары
        mock_products_data = self.generate_mock_products()
        
        # Создаем список Product объектов для MockShop
        mock_products = []
        for listing_id, url in mock_products_data.items():
            product = Product(
                listing_id=listing_id,
                title=f"Mock Product {listing_id}",
                url=url,
                shop_name="MockShop",
                price="25.00",
                currency="USD"
            )
            mock_products.append(product)
        
        # Добавляем MockShop к результатам
        all_shop_products["MockShop"] = mock_products
        print(f"Добавлен моковый магазин MockShop с {len(mock_products)} товарами")
        
        return all_shop_products
    
    def save_results_with_new_products(self, all_shop_products: Dict[str, List[Product]], new_products: Dict[str, str]) -> str:
        """Сохраняет результаты с информацией о новых товарах в папку текущего сеанса парсинга"""
        # Используем папку текущего сеанса парсинга или создаём новую
        if not self.current_parsing_dir:
            self.start_parsing_session()
        
        results_file = os.path.join(self.current_parsing_dir, "results.json")
        
        # Формируем структуру данных
        shops_data = {}
        for shop_name, products in all_shop_products.items():
            shops_data[shop_name] = {product.listing_id: product.url for product in products}
        
        results = {
            "shops": shops_data,
            "new_products": new_products
        }
        
        # Сохраняем в JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Результаты с новыми товарами сохранены в файл: {results_file}")
        
        # Сохраняем новые товары в Google Sheets
        self.save_new_products_to_sheets(new_products)
        
        return results_file
    
    def save_new_products_to_sheets(self, new_products: Dict[str, str]):
        """Сохраняет новые товары в Google Sheets"""
        if not new_products:
            return
        
        # Проверяем, включена ли интеграция с Google Sheets
        if hasattr(self.config, 'google_sheets_enabled') and self.config.google_sheets_enabled:
            try:
                from services.google_sheets_service import GoogleSheetsService
                sheets_service = GoogleSheetsService(self.config)
                
                if sheets_service.enabled:
                    sheets_service.add_new_products_to_sheets(
                        self.config.google_sheets_spreadsheet_id,
                        new_products,
                        "Etsy Products"
                    )
                else:
                    print("⚠️ Google Sheets не настроен, пропускаем сохранение новых товаров")
            except Exception as e:
                print(f"⚠️ Ошибка сохранения новых товаров в Google Sheets: {e}")
        else:
            print("📊 Google Sheets отключен в конфигурации")
    
    def delete_previous_parsing_folder(self) -> bool:
        """Удаляет предыдущую папку парсинга с повторными попытками"""
        previous_results_file = self.get_previous_results_file()
        
        if not previous_results_file:
            print("Нет предыдущей папки для удаления")
            return True
        
        # Получаем путь к папке из пути к файлу
        previous_folder = os.path.dirname(previous_results_file)
        
        if not os.path.exists(previous_folder):
            print(f"Папка {previous_folder} уже не существует")
            return True
        
        print(f"Попытка удаления папки: {previous_folder}")
        
        # Пытаемся удалить папку с повторными попытками
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                # Принудительно закрываем все файловые дескрипторы
                import gc
                gc.collect()
                
                # Дополнительная пауза для освобождения ресурсов
                import time
                time.sleep(1)
                
                # Сначала пытаемся изменить права доступа к файлам (для Windows)
                if os.name == 'nt':  # Windows
                    import stat
                    for root, dirs, files in os.walk(previous_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, stat.S_IWRITE)
                            except:
                                pass
                
                # Удаляем папку целиком
                shutil.rmtree(previous_folder, ignore_errors=False)
                
                # Проверяем, что папка действительно удалена
                if not os.path.exists(previous_folder):
                    print(f"✅ Предыдущая папка успешно удалена: {previous_folder}")
                    return True
                else:
                    print(f"⚠️ Папка все еще существует после удаления")
                    
            except PermissionError as e:
                if attempt < max_attempts - 1:
                    print(f"Попытка {attempt + 1}/{max_attempts}: файлы заблокированы, ожидание 3 секунды...")
                    time.sleep(3)
                else:
                    print(f"❌ Не удалось удалить папку {previous_folder}: файлы заблокированы")
                    print("Возможные причины:")
                    print("- Файлы Excel открыты в другой программе")
                    print("- Папка используется другим процессом")
                    print("- Недостаточно прав доступа")
                    
                    # Попытка альтернативного удаления через командную строку Windows
                    if os.name == 'nt':
                        try:
                            import subprocess
                            result = subprocess.run(['rmdir', '/s', '/q', previous_folder], 
                                                  shell=True, capture_output=True, text=True)
                            if result.returncode == 0 and not os.path.exists(previous_folder):
                                print(f"✅ Папка удалена через системную команду: {previous_folder}")
                                return True
                        except Exception as cmd_error:
                            print(f"Системная команда также не сработала: {cmd_error}")
                    
                    return False
                    
            except Exception as e:
                print(f"❌ Неожиданная ошибка при удалении папки {previous_folder}: {e}")
                if attempt < max_attempts - 1:
                    print(f"Повторная попытка через 2 секунды...")
                    time.sleep(2)
                else:
                    return False
        
        return False
    
    def load_shop_urls(self, links_file: str = None) -> List[str]:
        """Загружает список URL магазинов из Google Sheets или файла"""
        # Сначала пытаемся загрузить из Google Sheets
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
                        print(f"📊 Загружено {len(urls)} URL магазинов из Google Sheets")
                        return urls
                    else:
                        print("⚠️ Google Sheets пуст, используем локальный файл")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки из Google Sheets: {e}")
                print("📁 Переключаемся на локальный файл")
        
        # Fallback на локальный файл
        if links_file is None:
            links_file = self.config.links_file
        
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"📁 Загружено {len(urls)} URL магазинов из локального файла")
            return urls
            
        except FileNotFoundError:
            print(f"❌ Файл {links_file} не найден")
            return []
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {links_file}: {e}")
            return []