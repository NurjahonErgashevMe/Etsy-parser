"""
Сервис для работы с Google Sheets
"""
import gspread
from google.auth.exceptions import GoogleAuthError
from datetime import datetime
from typing import List, Dict, Optional

class GoogleSheetsService:
    """Сервис для работы с Google Таблицами"""
    
    def __init__(self, config):
        self.config = config
        self.credentials_file = config.google_sheets_credentials or "credentials.json"
        self.client = None
        self.enabled = self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Инициализирует клиент Google Sheets"""
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
        """Загружает список URL магазинов из Google Таблицы"""
        if not self.enabled:
            print("⚠️ Google Sheets не настроен, используем локальный файл")
            return []
        
        try:
            print(f"📊 Загрузка URL магазинов из листа '{sheet_name}'...")
            
            # Открываем таблицу
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Получаем все значения из столбца A (начиная со 2 строки, пропуская заголовок)
            values = worksheet.col_values(1)  # Столбец A
            
            # Фильтруем пустые строки и заголовки
            urls = []
            for value in values[1:]:  # Пропускаем первую строку (заголовок)
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
    
    def add_new_products_to_sheets(self, spreadsheet_id: str, new_products: Dict[str, str], sheet_name: str = "Etsy Products"):
        """Добавляет новые товары в Google Таблицу"""
        if not self.enabled:
            print("⚠️ Google Sheets не настроен, пропускаем сохранение")
            return
        
        if not new_products:
            print("📊 Нет новых товаров для добавления в Google Sheets")
            return
        
        try:
            print(f"📊 Добавление {len(new_products)} новых товаров в лист '{sheet_name}'...")
            
            # Открываем таблицу
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                # Создаём лист если его нет
                print(f"📊 Создание нового листа '{sheet_name}'...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=2)
                # Добавляем заголовки
                worksheet.update('A1:B1', [['Ссылки на товары', 'Время обнаружения']])
            
            # Получаем текущее время
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            rows_to_add = []
            for listing_id, url in new_products.items():
                rows_to_add.append([url, current_time])
            
            existing_data = worksheet.get_all_values()[1:]  

            all_data = rows_to_add + existing_data
            
            if all_data:
                # Очищаем данные начиная со второй строки
                worksheet.batch_clear([f'A2:B{len(existing_data) + len(rows_to_add) + 1}'])
                
                # Записываем все данные (новые сверху)
                range_name = f'A2:B{len(all_data) + 1}'
                worksheet.update(range_name, all_data)
                
                print(f"✅ Добавлено {len(rows_to_add)} новых товаров в Google Sheets (сверху)")
                print(f"📊 Общее количество записей: {len(all_data)}")
                print(f"📊 Диапазон: {range_name}")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении товаров в Google Sheets: {e}")
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        """Тестирует подключение к Google Sheets"""
        if not self.enabled:
            return False
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            print(f"✅ Подключение к таблице '{spreadsheet.title}' успешно")
            
            # Показываем доступные листы
            worksheets = spreadsheet.worksheets()
            print(f"📊 Доступные листы: {[ws.title for ws in worksheets]}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Sheets: {e}")
            return False