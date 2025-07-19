# Etsy Shop Monitor

Система мониторинга магазинов Etsy с отслеживанием изменений товаров и уведомлениями.

## 🏗️ Архитектура

Проект построен по модульной архитектуре с разделением ответственности:

```
├── config.py                 # Конфигурация приложения
├── main.py                   # Главный модуль и точка входа
├── scheduler.py              # Планировщик для автоматического запуска
├── requirements.txt          # Зависимости Python
├── links.txt                 # Список URL магазинов для мониторинга
│
├── models/                   # Модели данных
│   └── product.py           # Модели Product и ShopComparison
│
├── parsers/                  # Парсеры для разных платформ
│   ├── __init__.py
│   ├── base_parser.py       # Базовый класс для всех парсеров
│   └── etsy_parser.py       # Парсер для Etsy
│
├── services/                 # Бизнес-логика и внешние сервисы
│   ├── __init__.py
│   ├── data_service.py      # Работа с данными (сохранение/загрузка)
│   ├── telegram_service.py  # Telegram уведомления (заглушка)
│   └── google_sheets_service.py # Google Sheets интеграция (заглушка)
│
├── output/                   # Результаты парсинга (Excel файлы)
└── logs/                     # Логи приложения
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка списка магазинов

Добавьте URL магазинов в файл `links.txt`:

```
https://www.etsy.com/shop/PiondressShop
https://www.etsy.com/shop/AnotherShop
```

### 3. Запуск парсинга

```bash
python main.py
```

### 4. Запуск с планировщиком

```bash
python scheduler.py
```

## 📊 Функциональность

### Текущие возможности

- ✅ Парсинг магазинов Etsy с обходом блокировок
- ✅ Извлечение данных о товарах (ID, название, ссылка, цена)
- ✅ Сохранение результатов в Excel файлы
- ✅ Сравнение с предыдущими результатами
- ✅ Определение новых и удаленных товаров
- ✅ Планировщик для автоматического запуска

### Планируемые фичи

- 🔄 Telegram бот для уведомлений
- 🔄 Интеграция с Google Sheets
- 🔄 Веб-интерфейс для управления
- 🔄 Поддержка других платформ

## 🔧 Конфигурация

Основные настройки находятся в `config.py`:

```python
@dataclass
class AppConfig:
    links_file: str = "links.txt"           # Файл со ссылками
    output_dir: str = "output"              # Папка для результатов
    check_interval_hours: int = 24          # Интервал проверки
    scheduler_enabled: bool = False         # Включить планировщик
    
    # Настройки Etsy парсера
    etsy: EtsyConfig = EtsyConfig(
        request_timeout=30,                 # Таймаут запросов
        request_delay=2,                    # Задержка между запросами
        max_retries=3                       # Количество повторов
    )
```

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
from main import EtsyMonitor

monitor = EtsyMonitor()
result = monitor.parse_single_shop("https://www.etsy.com/shop/PiondressShop")
```

### Парсинг всех магазинов

```python
monitor = EtsyMonitor()
results = monitor.parse_all_shops()
```

### Работа с данными

```python
from services.data_service import DataService
from config import config

data_service = DataService(config)

# Загрузка URL из файла
urls = data_service.load_shop_urls()

# Сравнение данных
comparison = data_service.compare_shop_data(products, "ShopName")
```

## 📈 Мониторинг и логи

Логи сохраняются в папку `logs/`:
- `scheduler.log` - логи планировщика

Результаты парсинга сохраняются в папку `output/` в формате:
- `{ShopName}_{DD.MM.YYYY_HH.MM.SS}.xlsx`

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