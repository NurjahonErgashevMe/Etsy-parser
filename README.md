# Etsy Parser

Автоматизированный парсер магазинов Etsy с GUI интерфейсом, Telegram ботом и интеграцией с Google Sheets.

## Возможности

- **Парсинг магазинов Etsy** - автоматический сбор данных о товарах
- **GUI интерфейс** - удобное управление через графический интерфейс
- **Telegram бот** - уведомления о новых товарах и управление парсингом
- **Google Sheets** - экспорт данных в таблицы Google
- **Мониторинг изменений** - отслеживание новых товаров в магазинах
- **Обход блокировок** - автоматическая смена прокси при блокировке
- **Планировщик** - автоматический запуск парсинга по расписанию

## Структура проекта

```
sacsca/
├── bot/                    # Telegram бот
├── core/                   # Основная логика мониторинга
├── gui/                    # Графический интерфейс
├── parsers/                # Парсеры для Etsy
├── services/               # Сервисы (браузер, данные, Google Sheets)
├── models/                 # Модели данных
├── utils/                  # Утилиты
├── config/                 # Конфигурация
├── output/                 # Результаты парсинга
│   ├── parsing/            # Новинки (результаты парсинга)
│   └── xits/               # Хиты продаж
└── logs/                   # Логи приложения
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd sacsca
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте конфигурацию:
   - Создайте файл `.env` с настройками бота
   - Добавьте `credentials.json` для Google Sheets API
   - Настройте список магазинов в `config-main.txt`

## Использование

### GUI режим
```bash
python main.py
```

### Разовый парсинг
```bash
python app.py
```

### Telegram бот
```bash
python bot.py
```

## Конфигурация

### Переменные окружения (config-main.txt)
```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
EVERBEE_USERNAME=your_everbee_email
EVERBEE_PASSWORD=your_everbee_password

# URL магазинов для парсинга
https://www.etsy.com/shop/ShopName1
https://www.etsy.com/shop/ShopName2
```

### Google Sheets API
Поместите файл `credentials.json` с ключами сервисного аккаунта Google в корень проекта.

### Прокси (опционально)
Добавьте прокси в файл `proxies.txt` в формате:
```
ip:port:username:password
```

## Основные компоненты

### EverBeeParser
- Парсинг товаров через EverBee API
- Сортировка по новизне (новые товары сначала)
- Получение только товаров за последний месяц
- Быстрый и стабильный парсинг без блокировок

### EtsyMonitor
- Мониторинг изменений в магазинах
- Сравнение с предыдущими результатами
- Сохранение данных в Excel и JSON

### Telegram Bot
- Уведомления о новых товарах
- Управление парсингом
- Планировщик задач
- Администрирование

### GUI
- Визуальное управление парсингом
- Просмотр логов
- Настройка конфигурации

## Форматы вывода

- **Excel файлы** (`output/parsing/`) - детальные данные по каждому магазину
- **JSON файлы** (`output/parsing/`) - структурированные данные для обработки
- **Google Sheets** - онлайн таблицы с результатами
- **Хиты продаж** (`output/xits/`) - папка для будущей функциональности

## Миграция структуры папок

Если у вас есть старые данные в папке `output/`, выполните миграцию:

```bash
python migrate_folders.py
```

Подробнее см. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## Требования

- Python 3.8+
- Chrome/Chromium браузер
- Telegram Bot Token (для бота)
- Google Service Account (для Sheets)

## Лицензия

MIT License