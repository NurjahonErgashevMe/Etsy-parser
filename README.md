# Etsy Shop Monitor

Система мониторинга магазинов Etsy с отслеживанием изменений товаров, автоматическим планировщиком и интеграцией с Google Sheets.

## 🏗️ Архитектура

Проект построен по модульной архитектуре с разделением ответственности:

```
├── app.py                    # Flask веб-приложение
├── main.py                   # Главный модуль и точка входа
├── credentials.json          # Учетные данные Google Sheets
├── requirements.txt          # Зависимости Python
├── test_google_sheets.py     # Тесты Google Sheets интеграции
│
├── config/                   # Конфигурация
│   ├── __init__.py
│   └── settings.py          # Настройки приложения
│
├── core/                     # Основная логика
│   ├── __init__.py
│   ├── monitor.py           # Главный класс мониторинга
│   └── scheduler.py         # Планировщик задач
│
├── models/                   # Модели данных
│   └── product.py           # Модели Product и ShopComparison
│
├── parsers/                  # Парсеры для разных платформ
│   ├── __init__.py
│   ├── base_parser.py       # Базовый класс для всех парсеров
│   └── etsy_parser.py       # Парсер для Etsy с Selenium
│
├── services/                 # Бизнес-логика и внешние сервисы
│   ├── __init__.py
│   ├── browser_service.py   # Управление браузером Selenium
│   ├── data_service.py      # Работа с данными (сохранение/загрузка)
│   └── google_sheets_service.py # Google Sheets интеграция
│
├── output/                   # Результаты парсинга по датам
│   └── DD.MM.YYYY_HH.MM/    # Папки с результатами сеансов
│       ├── {ShopName}.xlsx  # Excel файлы по магазинам
│       └── results.json     # Сводные результаты с новыми товарами
│
└── logs/                     # Логи приложения
    └── scheduler.log        # Логи планировщика
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка Google Sheets (опционально)

1. Поместите файл `credentials.json` с учетными данными Google API в корень проекта
2. Обновите `google_sheets_spreadsheet_id` в `config/settings.py`
3. Создайте листы "Etsy Shops" (для URL магазинов) и "Etsy Products" (для результатов)

### 3. Настройка списка магазинов

**Вариант A: Google Sheets (рекомендуется)**
- Добавьте URL магазинов в лист "Etsy Shops" вашей таблицы

**Вариант B: Локальный файл**
- Создайте файл `links.txt` и добавьте URL:
```
https://www.etsy.com/shop/PiondressShop
https://www.etsy.com/shop/mimetik
```

### 4. Запуск парсинга

```bash
# Разовый запуск
python main.py

# Запуск с автоматическим планировщиком
python core/scheduler.py

# Веб-интерфейс (в разработке)
python app.py
```

## 📊 Функциональность

### Текущие возможности

- ✅ Парсинг магазинов Etsy с использованием Selenium WebDriver
- ✅ Обход блокировок и антибот-защиты
- ✅ Извлечение данных о товарах (ID, название, ссылка, цена, изображения)
- ✅ Сохранение результатов в Excel файлы по датам
- ✅ Сравнение с предыдущими результатами и определение новых товаров
- ✅ Интеграция с Google Sheets для управления списком магазинов
- ✅ Автоматическое сохранение новых товаров в Google Sheets
- ✅ Планировщик для автоматического запуска (каждые 3 минуты для тестирования)
- ✅ Система управления сеансами парсинга с автоочисткой старых данных
- ✅ Обработка MockShop для тестирования функциональности

### Особенности логики новых товаров

- 🔍 **Новые магазины**: При добавлении нового магазина его товары НЕ считаются "новыми" в первом запуске
- 🔍 **Сравнение**: Новыми считаются только товары, появившиеся в уже отслеживаемых магазинах
- 🔍 **MockShop**: Автоматически добавляется для демонстрации функциональности

### Планируемые фичи

- 🔄 Telegram бот для уведомлений о новых товарах
- 🔄 Веб-интерфейс для управления и мониторинга
- 🔄 Поддержка других платформ (Amazon, eBay)
- 🔄 Настройка фильтров по категориям и ценам
- 🔄 Экспорт в различные форматы (CSV, JSON, PDF)

## 🔧 Конфигурация

Основные настройки находятся в `config/settings.py`:

```python
@dataclass
class AppConfig:
    # Пути к файлам и папкам
    links_file: str = "links.txt"
    output_dir: str = "output"
    logs_dir: str = "logs"
    
    # Google Sheets настройки
    google_sheets_enabled: bool = True
    google_sheets_credentials: str = "credentials.json"
    google_sheets_spreadsheet_id: str = "YOUR_SPREADSHEET_ID"
    
    # Настройки планировщика
    scheduler_enabled: bool = True
    check_interval_hours: float = 0.05      # Каждые 3 минуты для тестирования
    
    # Настройки Etsy парсера
    etsy: EtsyConfig = EtsyConfig(
        base_url="https://www.etsy.com",
        request_delay=2,                    # Задержка между страницами
        max_retries=3,                      # Количество попыток перезагрузки браузера
        page_load_timeout=90                # Таймаут ожидания загрузки страницы
    )
```

### Настройка Google Sheets

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Google Sheets API
3. Создайте Service Account и скачайте `credentials.json`
4. Поделитесь таблицей с email из Service Account
5. Обновите `google_sheets_spreadsheet_id` в настройках

## 📁 Структура данных

### Модель Product

```python
@dataclass
class Product:
    listing_id: str      # ID товара на Etsy
    title: str          # Название товара
    url: str            # Ссылка на товар
    shop_name: str      # Название магазина
    price: str          # Цена (опционально)
    currency: str       # Валюта (опционально)
    image_url: str      # Ссылка на изображение (опционально)
    scraped_at: datetime # Время парсинга
```

### Результаты сравнения

```python
@dataclass
class ShopComparison:
    shop_name: str              # Название магазина
    new_products: List[Product] # Новые товары
    removed_products: List[Product] # Удаленные товары
    total_current: int          # Текущее количество
    total_previous: int         # Предыдущее количество
    comparison_date: datetime   # Дата сравнения
```

## 🔍 Использование

### Парсинг одного магазина

```python
from core.monitor import EtsyMonitor

monitor = EtsyMonitor()
result = monitor.parse_single_shop("https://www.etsy.com/shop/PiondressShop")
```

### Парсинг всех магазинов с автоматическим сравнением

```python
monitor = EtsyMonitor()
monitor.run_monitoring_cycle()  # Полный цикл с сравнением и сохранением
```

### Работа с данными

```python
from services.data_service import DataService
from config.settings import config

data_service = DataService(config)

# Загрузка URL из Google Sheets или локального файла
urls = data_service.load_shop_urls()

# Сравнение данных магазина
comparison = data_service.compare_shop_data(products, "ShopName")

# Сравнение всех результатов и поиск новых товаров
new_products = data_service.compare_all_shops_results(current_results)
```

### Работа с Google Sheets

```python
from services.google_sheets_service import GoogleSheetsService

sheets_service = GoogleSheetsService(config)

# Загрузка списка магазинов
urls = sheets_service.load_shop_urls_from_sheets(spreadsheet_id, "Etsy Shops")

# Сохранение новых товаров
sheets_service.add_new_products_to_sheets(spreadsheet_id, new_products, "Etsy Products")
```

## 📈 Мониторинг и логи

### Логи
Логи сохраняются в папку `logs/`:
- `scheduler.log` - логи планировщика с информацией о запусках

### Результаты парсинга
Результаты сохраняются в папку `output/` по структуре:
```
output/
├── 23.07.2025_15.50/        # Папка сеанса парсинга
│   ├── PiondressShop.xlsx   # Excel файл магазина
│   ├── mimetik.xlsx         # Excel файл магазина
│   ├── MockShop.xlsx        # Тестовый магазин
│   └── results.json         # Сводные результаты с новыми товарами
└── 23.07.2025_12.30/        # Предыдущий сеанс (автоматически удаляется)
```

### Структура results.json
```json
{
  "shops": {
    "PiondressShop": {
      "1899100733": "https://www.etsy.com/listing/1899100733/...",
      "1891621493": "https://www.etsy.com/listing/1891621493/..."
    }
  },
  "new_products": {
    "1234567890": "https://www.etsy.com/listing/1234567890/..."
  }
}
```

## 🛠️ Расширение функциональности

### Добавление нового парсера

1. Создайте класс, наследующий от `BaseParser`
2. Реализуйте методы `parse_shop_page()` и `get_shop_name_from_url()`
3. Добавьте парсер в `main.py`

### Добавление нового сервиса

1. Создайте класс в папке `services/`
2. Добавьте конфигурацию в `config.py`
3. Интегрируйте с основным циклом в `main.py`

## 🔒 Безопасность

- Используются реальные User-Agent и headers для обхода блокировок
- Настраиваемые задержки между запросами
- Обработка ошибок и повторные попытки
- Логирование всех операций

## 📝 Примечания

- Cookies в конфигурации могут устареть, при необходимости обновите их
- Рекомендуется использовать VPN при интенсивном парсинге
- Соблюдайте robots.txt и условия использования Etsy