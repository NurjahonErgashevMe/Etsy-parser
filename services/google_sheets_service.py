import gspread
from google.auth.exceptions import GoogleAuthError
from datetime import datetime
from typing import List, Dict, Optional
from utils.shop_helpers import get_shop_name_for_product, extract_shop_names_from_results

class GoogleSheetsService:
    
    def __init__(self, config):
        self.config = config
        self.credentials_file = config.google_sheets_credentials or "credentials.json"
        self.client = None
        self.enabled = self._initialize_client()
    
    def _initialize_client(self) -> bool:
        try:
            self.client = gspread.service_account(filename=self.credentials_file)
            print(f"✅ Google Sheets клиент успешно инициализирован")
            return True
        except FileNotFoundError:
            print(f"❌ Файл credentials не найден: {self.credentials_file}")
            return False
        except GoogleAuthError as e:
            print(f"❌ Ошибка аутентификации Google: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Sheets: {e}")
            return False
    
    def load_shop_urls_from_sheets(self, spreadsheet_id: str, sheet_name: str = "Etsy Shops") -> List[str]:
        if not self.enabled:
            print("⚠️ Google Sheets не настроен, используем локальный файл")
            return []
        
        try:
            print(f"📊 Загрузка URL магазинов из листа '{sheet_name}'...")
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            values = worksheet.col_values(1)
            
            urls = []
            for value in values[1:]:
                if value and value.strip() and value.startswith('http'):
                    urls.append(value.strip())
            
            print(f"✅ Загружено {len(urls)} URL магазинов из Google Sheets")
            return urls
            
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{sheet_name}' не найден в таблице")
            return []
        except Exception as e:
            print(f"❌ Ошибка при загрузке URL из Google Sheets: {e}")
            return []
    
    def add_new_products_to_sheets(self, spreadsheet_id: str, new_products: Dict[str, str], sheet_name: str = "Etsy Products", results: Dict = None):
        if not self.enabled:
            print("⚠️ Google Sheets не настроен, пропускаем сохранение")
            return
        
        if not new_products:
            print("📊 Нет новых товаров для добавления в Google Sheets")
            return
        
        try:
            print(f"📊 Добавление {len(new_products)} новых товаров в лист '{sheet_name}'...")
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                print(f"📊 Создание нового листа '{sheet_name}'...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=3)
                worksheet.update('A1:C1', [['Ссылки на товары', 'Время обнаружения', 'Название магазина']])
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                existing_urls = {
                    value.strip()
                    for value in worksheet.col_values(1)[1:]
                    if value and value.strip()
                }
            except Exception:
                existing_urls = set()
            
            rows_to_add = []
            for listing_id, url in new_products.items():
                if url in existing_urls:
                    continue
                
                shop_name = get_shop_name_for_product(listing_id, url, results)
                rows_to_add.append([url, current_time, shop_name])
                existing_urls.add(url)
            
            if not rows_to_add:
                print("📊 Все найденные новинки уже есть в Google Sheets")
                return
            
            chunk_size = 100
            for start in range(len(rows_to_add), 0, -chunk_size):
                chunk = rows_to_add[max(0, start - chunk_size):start]
                worksheet.insert_rows(
                    chunk,
                    row=2,
                    value_input_option='USER_ENTERED'
                )
            
            print(f"✅ Добавлено {len(rows_to_add)} новых товаров в Google Sheets (сверху)")
            added_shops = {row[2] for row in rows_to_add}
            print(f"📊 Добавлены товары из магазинов: {', '.join(added_shops)}")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении товаров в Google Sheets: {e}")
    
    def add_top_listings_to_sheets(self, spreadsheet_id: str, top_listings: Dict, sheet_name: str = "Top Listings"):
        if not self.enabled:
            print("⚠️ Google Sheets не настроен, пропускаем сохранение")
            return
        
        if not top_listings:
            print("📊 Нет топ-листингов для добавления в Google Sheets")
            return
        
        try:
            print(f"📊 Добавление {len(top_listings)} топ-хитов в лист '{sheet_name}'...")
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                # Ensure we have enough columns (10)
                try:
                    if worksheet.col_count < 10:
                        worksheet.resize(cols=10)
                except:
                    pass
            except gspread.WorksheetNotFound:
                print(f"📊 Создание нового листа '{sheet_name}'...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
                worksheet.update('A1:J1', [[
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
                ]])
            
            rows_to_add = []
            for listing_id, data in top_listings.items():
                # Конвертируем формат даты из "12.10.2025_15.29" в "2025-10-12 15:29"
                def convert_date(date_str):
                    try:
                        dt = datetime.strptime(date_str, "%d.%m.%Y_%H.%M")
                        return dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        return date_str
                
                # Принудительно конвертируем в числа (убираем апострофы и строки)
                def to_int(val):
                    try:
                        return int(str(val).replace("'", "").strip())
                    except:
                        return 0
                
                def to_float(val):
                    try:
                        return float(str(val).replace("'", "").strip())
                    except:
                        return 0.0
                
                views_start = to_int(data.get('views_start', 0))
                views_hit = to_int(data.get('views_hit', 0))
                views_daily = to_float(data.get('views_daily_growth', 0.0))
                
                likes_start = to_int(data.get('likes_start', 0))
                likes_hit = to_int(data.get('likes_hit', 0))
                likes_daily = to_float(data.get('likes_daily_growth', 0.0))
                
                reviews = to_int(data.get('reviews', 0))

                rows_to_add.append([
                    data['url'],
                    convert_date(data['discovered_at']),
                    convert_date(data['became_hit_at']),
                    views_start,
                    views_hit,
                    views_daily,
                    likes_start,
                    likes_hit,
                    likes_daily,
                    reviews
                ])
            
            # Get existing data and normalize to 10 columns
            existing_data = worksheet.get_all_values()[1:]
            normalized_existing = []
            for row in existing_data:
                if len(row) < 10:
                    # Pad with 0 for missing columns
                    row = row + [0] * (10 - len(row))
                elif len(row) > 10:
                    # Trim to 10 columns
                    row = row[:10]
                normalized_existing.append(row)
            
            all_data = rows_to_add + normalized_existing
            
            if all_data:
                worksheet.batch_clear([f'A2:J{len(all_data) + 1}'])
                range_name = f'A2:J{len(all_data) + 1}'
                worksheet.update(range_name, all_data)
                
                print(f"✅ Добавлено {len(rows_to_add)} топ-хитов в Google Sheets (сверху)")
                print(f"📊 Общее количество записей: {len(all_data)}")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении топ-хитов в Google Sheets: {e}")
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            print(f"✅ Подключение к таблице '{spreadsheet.title}' успешно")
            
            worksheets = spreadsheet.worksheets()
            print(f"📊 Доступные листы: {[ws.title for ws in worksheets]}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Sheets: {e}")
            return False