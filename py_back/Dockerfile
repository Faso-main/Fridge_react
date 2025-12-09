FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Обновляем main.py для работы с Docker
RUN sed -i "s/host=\"localhost\"/host=os.getenv('DB_HOST', 'localhost')/" main.py && \
    sed -i "s/port=\"5432\"/port=os.getenv('DB_PORT', '5432')/" main.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]