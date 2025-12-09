# Используем более новую версию Node.js для совместимости с Vite
FROM node:20-alpine as build

WORKDIR /app

# Копируем файлы зависимостей
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходный код
COPY . .

# Проверяем структуру проекта
RUN echo "Проверка структуры проекта:" && ls -la && \
    echo "Проверка index.html:" && cat index.html | grep -A5 -B5 "Main" && \
    echo "Проверка vite.config.js:" && cat vite.config.js || echo "vite.config.js не найден"

# Сборка приложения
RUN npm run build

# Проверяем результат сборки
RUN echo "Результат сборки:" && ls -la dist/

# Production этап
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

# Базовая конфигурация nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]