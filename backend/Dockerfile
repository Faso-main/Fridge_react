FROM node:18-alpine

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Копирование исходного кода
COPY . .

# Изменяем server.js для работы с Docker
RUN sed -i "s/host: 'localhost'/host: process.env.DB_HOST || 'localhost'/" server.js

EXPOSE 5000

CMD ["node", "server.js"]