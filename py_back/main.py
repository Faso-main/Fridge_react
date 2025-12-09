from contextlib import closing
from datetime import datetime
from typing import List, Dict, Any

import os
import sys
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Database Python API", version="1.0.0")

RESOURCE = "api"

# CORS. В бою лучше явно указать допустимые домены.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ItemCreate(BaseModel):
    name: str
    isInFridge: bool = True


class ItemResponse(BaseModel):
    id: int
    name: str
    is_in_fridge: bool
    created_at: datetime
    category: str


class SearchRequest(BaseModel):
    query: str


DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "fridge_db"),
    "user": os.getenv("DB_USER", "fridge_user"),
    "password": os.getenv("DB_PASSWORD", "1234"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
}


def get_db_connection(
    max_retries: int = 5, delay: int = 5
) -> psycopg2.extensions.connection:
    """Подключение к базе данных с повторами."""
    print(
        f"Подключение к БД: host={DB_CONFIG['host']}, db={DB_CONFIG['dbname']}, user={DB_CONFIG['user']}"
    )

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=DB_CONFIG["dbname"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
            )
            print(f"Подключение к БД успешно (попытка {attempt + 1}/{max_retries})")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Ошибка подключения к БД: {e}. Повтор через {delay} секунд.")
                time.sleep(delay)
            else:
                print(
                    f"Не удалось подключиться к базе данных после {max_retries} попыток: {e}"
                )
                raise
        except Exception as e:
            print(f"Непредвиденная ошибка подключения: {e}")
            raise

    raise ConnectionError("Не удалось установить соединение с базой данных")


PRODUCT_CATEGORIES: Dict[str, List[str]] = {
    "молочные": ["молоко", "сыр", "йогурт", "кефир", "творог", "сметана", "масло", "сливки"],
    "овощи": ["помидор", "огурец", "картофель", "морковь", "лук", "капуста", "перец"],
    "фрукты": ["яблоко", "банан", "апельсин", "лимон", "груша", "виноград"],
    "мясо": ["колбаса", "сосиски", "курица", "говядина", "свинина", "ветчина"],
    "напитки": ["сок", "вода", "чай", "кофе", "лимонад", "компот"],
    "хлеб": ["хлеб", "батон", "булка", "лаваш", "сухари"],
    "яйца": ["яйца", "яичница", "омлет"],
}


def categorize_product(product_name: str) -> str:
    """Простейшая категоризация по названию."""
    if not product_name:
        return "другое"

    product_lower = product_name.lower()
    for category, keywords in PRODUCT_CATEGORIES.items():
        if any(keyword in product_lower for keyword in keywords):
            return category
    return "другое"


@app.on_event("startup")
async def startup_event():
    """Инициализация приложения и проверка схемы БД."""

    print("Запуск Python Database API")
    print(f"Время запуска: {datetime.now().isoformat()}")
    print("Параметры БД:")
    print(f"  Хост: {DB_CONFIG['host']}")
    print(f"  База: {DB_CONFIG['dbname']}")
    print(f"  Пользователь: {DB_CONFIG['user']}")


    try:
        conn = get_db_connection(max_retries=3)

        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'fridge_items'
                );
            """
            )
            result = cursor.fetchone()
            table_exists = result[0] if result else False

            if not table_exists:
                print("Таблица fridge_items не найдена. Создаём.")
                cursor.execute(
                    """
                    CREATE TABLE fridge_items (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        is_in_fridge BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
                )
                conn.commit()
                print("Таблица fridge_items создана")

        conn.close()
        print("Инициализация БД завершена")
    except Exception as e:
        print(f"Предупреждение при инициализации БД: {e}")
        print("Приложение продолжит работу, но доступ к БД может быть ограничен.")


@app.get("/")
async def root():
    return {
        "message": "Python Database API запущен",
        "service": "python-backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database_config": {
            "host": DB_CONFIG["host"],
            "database": DB_CONFIG["dbname"],
            "connected": True,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Информация о сервисе"},
            {"path": "/health", "method": "GET", "description": "Проверка здоровья"},
            {
                "path": f"/{RESOURCE}/database-items",
                "method": "GET",
                "description": "Получить все товары",
            },
            {
                "path": f"/{RESOURCE}/items/add",
                "method": "POST",
                "description": "Добавить товар",
            },
            {
                "path": f"/{RESOURCE}/categories",
                "method": "GET",
                "description": "Категории товаров",
            },
            {
                "path": f"/{RESOURCE}/statistics",
                "method": "GET",
                "description": "Статистика по категориям",
            },
        ],
    }


@app.get("/health")
async def health_check():
    """Простая проверка доступности API и БД."""
    try:
        conn = get_db_connection(max_retries=1)

        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT NOW() as db_time, version() as db_version")
            result = cursor.fetchone()
            db_time, db_version = result if result else (None, None)

        conn.close()

        return {
            "status": "healthy",
            "service": "python-api",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "connected",
                "time": db_time.isoformat() if hasattr(db_time, "isoformat") else str(db_time), # pyright: ignore[reportOptionalMemberAccess]
                "version": db_version.split(",")[0] if db_version else "unknown",
            },
            "memory_usage": f"{sys.getsizeof([]) / 1024:.2f} KB",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "python-api",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "disconnected",
                "error": str(e),
            },
            "message": "API работает, но база данных недоступна",
        }


@app.get(f"/{RESOURCE}/database-items", response_model=List[ItemResponse])
async def get_database_items():
    """Список товаров с вычисленными категориями."""
    try:
        conn = get_db_connection()

        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM fridge_items ORDER BY created_at DESC")
            items = cursor.fetchall() or []

        conn.close()

        processed_items = []
        for item in items:
            if item and "name" in item:
                processed = dict(item)
                processed["category"] = categorize_product(item["name"])
                processed_items.append(processed)

        print(f"Получено {len(processed_items)} записей из БД")
        return processed_items

    except Exception as e:
        print(f"Ошибка при получении списка товаров: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.post(f"/{RESOURCE}/items/add")
async def add_item(item_data: ItemCreate):
    """Создать новый товар."""
    try:
        name = item_data.name.strip()
        is_in_fridge = item_data.isInFridge

        if not name:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Название товара обязательно",
                },
            )

        conn = get_db_connection()

        try:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                cursor.execute(
                    "INSERT INTO fridge_items (name, is_in_fridge) "
                    "VALUES (%s, %s) RETURNING *",
                    (name, is_in_fridge),
                )
                new_item = cursor.fetchone()
                conn.commit()

            if not new_item:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Database error",
                        "message": "Не удалось создать запись",
                    },
                )

            response_item = dict(new_item)
            response_item["category"] = categorize_product(name)

            print(f"Добавлен товар: {name} (is_in_fridge={is_in_fridge})")

            return {
                "message": "Товар добавлен",
                "item": response_item,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при добавлении товара: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.patch(f"/{RESOURCE}/items/move/{{item_id}}/toggle")
async def toggle_item_position(item_id: int):
    """Инвертировать флаг is_in_fridge."""
    try:
        conn = get_db_connection()

        try:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                cursor.execute("SELECT * FROM fridge_items WHERE id = %s", (item_id,))
                current_item = cursor.fetchone()

                if not current_item:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "error": "Not found",
                            "message": f"Товар с ID {item_id} не найден",
                        },
                    )

                new_state = not current_item["is_in_fridge"]
                cursor.execute(
                    "UPDATE fridge_items SET is_in_fridge = %s "
                    "WHERE id = %s RETURNING *",
                    (new_state, item_id),
                )
                updated_item = cursor.fetchone()
                conn.commit()

            if not updated_item:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Database error",
                        "message": "Не удалось обновить запись",
                    },
                )

            response_item = dict(updated_item)
            response_item["category"] = categorize_product(updated_item["name"])

            return {
                "message": "Состояние товара обновлено",
                "item": response_item,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при обновлении товара: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.delete(f"/{RESOURCE}/items/remove/{{item_id}}")
async def delete_item(item_id: int):
    """Удалить товар по ID."""
    try:
        conn = get_db_connection()

        try:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                cursor.execute("SELECT * FROM fridge_items WHERE id = %s", (item_id,))
                item = cursor.fetchone()

                if not item:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "error": "Not found",
                            "message": f"Товар с ID {item_id} не найден",
                        },
                    )

                cursor.execute(
                    "DELETE FROM fridge_items WHERE id = %s RETURNING *", (item_id,)
                )
                deleted_item = cursor.fetchone()
                conn.commit()

            if not deleted_item:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Database error",
                        "message": "Не удалось удалить запись",
                    },
                )

            response_item = dict(deleted_item)
            response_item["category"] = categorize_product(deleted_item["name"])

            print(f"Удалён товар: {item['name']} (ID: {item_id})")

            return {
                "message": "Товар удалён",
                "deleted_item": response_item,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при удалении товара: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.get(f"/{RESOURCE}/filter-by-category/{{category}}")
async def filter_by_category(category: str):
    """Фильтрация списка по категории."""
    try:
        conn = get_db_connection()

        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM fridge_items ORDER BY created_at DESC")
            all_items = cursor.fetchall() or []

        conn.close()

        filtered_items = []
        for item in all_items:
            if item and "name" in item:
                item_category = categorize_product(item["name"])
                if category.lower() in item_category.lower():
                    processed = dict(item)
                    processed["category"] = item_category
                    filtered_items.append(processed)

        print(f"Найдено {len(filtered_items)} товаров в категории '{category}'")

        return {
            "category": category,
            "count": len(filtered_items),
            "items": filtered_items,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"Ошибка при фильтрации по категории: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.get(f"/{RESOURCE}/categories")
async def get_categories():
    """Список категорий и несколько примеров по каждой."""
    category_examples = {
        cat: PRODUCT_CATEGORIES[cat][:3] for cat in PRODUCT_CATEGORIES
    }

    return {
        "categories": list(PRODUCT_CATEGORIES.keys()),
        "total_categories": len(PRODUCT_CATEGORIES),
        "timestamp": datetime.now().isoformat(),
        "category_examples": category_examples,
    }


@app.post(f"/{RESOURCE}/search-products")
async def search_products(search_data: SearchRequest):
    """Поиск по названию или категории."""
    search_query = search_data.query.lower().strip()

    if not search_query:
        return {
            "error": "Validation error",
            "message": "Пустой поисковый запрос",
            "search_query": "",
            "found_count": 0,
            "items": [],
        }

    try:
        conn = get_db_connection()

        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM fridge_items ORDER BY created_at DESC")
            all_items = cursor.fetchall() or []

        conn.close()

        found_items = []
        for item in all_items:
            if item and "name" in item:
                item_category = categorize_product(item["name"])
                item_name_lower = item["name"].lower()
                category_keywords = PRODUCT_CATEGORIES.get(search_query, [])

                if (
                    search_query in item_category
                    or search_query in item_name_lower
                    or any(keyword in item_name_lower for keyword in category_keywords)
                ):
                    processed = dict(item)
                    processed["category"] = item_category
                    processed["match_type"] = (
                        "category" if search_query in item_category else "name"
                    )
                    found_items.append(processed)

        print(f"По запросу '{search_query}' найдено {len(found_items)} товаров")

        return {
            "search_query": search_query,
            "found_count": len(found_items),
            "items": found_items,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.get(f"/{RESOURCE}/statistics")
async def get_statistics():
    """Статистика по категориям."""
    try:
        conn = get_db_connection()

        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM fridge_items")
            all_items = cursor.fetchall() or []

        conn.close()

        category_stats: Dict[str, Dict[str, Any]] = {}
        for item in all_items:
            if item and "name" in item and "is_in_fridge" in item:
                category = categorize_product(item["name"])
                stats = category_stats.setdefault(
                    category,
                    {"total": 0, "in_fridge": 0, "out_of_fridge": 0},
                )
                stats["total"] += 1
                if item["is_in_fridge"]:
                    stats["in_fridge"] += 1
                else:
                    stats["out_of_fridge"] += 1

        for category, stats in category_stats.items():
            if stats["total"] > 0:
                stats["in_fridge_percentage"] = round(
                    stats["in_fridge"] / stats["total"] * 100, 1
                )
                stats["out_of_fridge_percentage"] = round(
                    stats["out_of_fridge"] / stats["total"] * 100, 1
                )

        total_in_fridge = sum(stats["in_fridge"] for stats in category_stats.values())
        total_out_of_fridge = sum(
            stats["out_of_fridge"] for stats in category_stats.values()
        )

        return {
            "total_products": len(all_items),
            "categories": category_stats,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_in_fridge": total_in_fridge,
                "total_out_of_fridge": total_out_of_fridge,
            },
        }

    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.get(f"/{RESOURCE}/test-connection")
async def test_connection():
    """Проверка соединения с БД и базовых запросов."""
    try:
        conn = get_db_connection()

        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM fridge_items")
            total_result = cursor.fetchone()
            total_items = total_result[0] if total_result else 0

            cursor.execute(
                "SELECT COUNT(*) FROM fridge_items WHERE is_in_fridge = true"
            )
            in_fridge_result = cursor.fetchone()
            in_fridge = in_fridge_result[0] if in_fridge_result else 0

            cursor.execute("SELECT version()")
            version_result = cursor.fetchone()
            db_version = version_result[0] if version_result else "unknown"

        conn.close()

        return {
            "status": "success",
            "database": {
                "version": db_version,
                "connection": "established",
                "total_items": total_items,
                "items_in_fridge": in_fridge,
                "items_out_of_fridge": total_items - in_fridge,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "database": {
                "connection": "failed",
                "error": str(e),
            },
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":

    print("Запуск Python Database API")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Хост: 0.0.0.0")
    print("Порт: 8000")


    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        access_log=True,
    )
