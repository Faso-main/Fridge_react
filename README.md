# Fridge Management System

Система управления продуктами в холодильнике с интеллектуальной категоризацией.
![решение в продакшене](readme/prod.png)
## Архитектура

- **Frontend**: React SPA
- **Backend**: Python FastAPI 
- **Database**: PostgreSQL
- **API**: RESTful JSON API

## Функциональность

- Управление продуктами (добавление/удаление/перемещение)
- Автоматическая категоризация продуктов
- Поиск по категориям и названиям
- Статистика по наличию продуктов
- Визуализация состояния холодильника

## API Endpoints

```
GET    /api/database-items     - Получить все продукты
POST   /api/items              - Добавить продукт
PATCH  /api/items/{id}/toggle  - Переместить продукт
DELETE /api/items/{id}         - Удалить продукт
POST   /api/search-products    - Поиск продуктов
GET    /api/categories         - Список категорий
GET    /api/statistics         - Статистика
```

## Технические требования

- Python 3.8+
- PostgreSQL 12+
- Node.js 16+

## Установка и запуск

```bash
# Бэкенд
pip install -r requirements.txt
python main.py

# Фронтенд
npm install
npm run dev
```
