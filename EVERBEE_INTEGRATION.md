# EverBee Integration

## Описание

Интеграция с EverBee API для получения детальной аналитики по новым листингам.

## Структура данных

### Формат файла `new_perspective_listings.json`

```json
{
  "listings": {
    "1772879674": {
      "11.08.2025_17.13": {
        "price": "144.25",
        "est_total_sales": 16,
        "est_mo_sales": 0,
        "listing_age_in_months": 12,
        "est_reviews": 6,
        "est_reviews_in_months": 1,
        "conversion_rate": 0.14,
        "views": 12101,
        "num_favorers": 178,
        "url": "https://www.etsy.com/listing/1772879674/..."
      },
      "18.08.2025_17.13": {
        "price": "144.25",
        "est_total_sales": 20,
        ...
      }
    }
  }
}
```

## Процесс работы

1. **Парсинг магазинов** → находим новые листинги
2. **Отправка в EverBee API** → batch запрос для всех новых листингов
3. **Извлечение данных** → только нужные поля
4. **Сохранение** → добавление с датой проверки в `new_perspective_listings.json`

## Отслеживаемые метрики

- `price` - цена товара
- `est_total_sales` - оценка общих продаж
- `est_mo_sales` - оценка продаж за месяц
- `listing_age_in_months` - возраст листинга в месяцах
- `est_reviews` - оценка отзывов
- `est_reviews_in_months` - отзывы за месяц
- `conversion_rate` - конверсия
- `views` - просмотры
- `num_favorers` - добавили в избранное
- `url` - ссылка на товар

## API Endpoint

**POST** `https://api.everbee.com/etsy_apis/listing`

**Headers:**
```json
{
  "x-access-token": "your_token"
}
```

**Body:**
```json
{
  "listing_ids": [["123", "456", "789"]]
}
```

**Response:**
```json
{
  "results": [...],
  "total_count": 100
}
```

## Конфигурация

В `config-main.txt`:
```
EVERBEE_USERNAME=your_email@example.com
EVERBEE_PASSWORD=your_password
```

Токен сохраняется автоматически после первой авторизации.
