const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const path = require('path');

const app = express();
const port = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Конфигурация подключения к PostgreSQL
const pool = new Pool({
  user: process.env.DB_USER || 'fridge_user',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'fridge_db',
  password: process.env.DB_PASSWORD || '1234',
  port: parseInt(process.env.DB_PORT) || 5432,
  // Параметры для Docker
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Проверка подключения к базе данных
const checkConnection = async () => {
  let retries = 5;
  while (retries) {
    try {
      await pool.query('SELECT NOW()');
      console.log('Подключение к базе данных установлено');
      break;
    } catch (err) {
      console.log(`Ошибка подключения к базе данных. Повторная попытка через 5 секунд... (${retries} попыток осталось)`);
      retries -= 1;
      await new Promise(res => setTimeout(res, 5000));
    }
  }
};

// Create table
const createTable = async () => {
  const query = `
    CREATE TABLE IF NOT EXISTS fridge_items (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      is_in_fridge BOOLEAN DEFAULT true,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  `;
  
  try {
    await pool.query(query);
    console.log('Таблица fridge_items готова');
  } catch (err) {
    console.error('Ошибка создания таблицы:', err.message);
  }
};

// Инициализация
const initializeApp = async () => {
  await checkConnection();
  await createTable();
  
  app.listen(port, () => {
    console.log(`Сервер запущен на http://localhost:${port}`);
  });
};

// Обработка ошибок базы данных
pool.on('error', (err) => {
  console.error('Неожиданная ошибка базы данных:', err.message);
});

// Health check
app.get('/api/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ 
      status: 'OK', 
      database: 'connected',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'ERROR', 
      database: 'disconnected',
      error: error.message 
    });
  }
});

// GET all items
app.get('/api/items', async (req, res) => {
  try {
    console.log('GET /api/items - получение всех продуктов');
    const result = await pool.query('SELECT * FROM fridge_items ORDER BY created_at DESC');
    console.log(`✅ Найдено продуктов: ${result.rows.length}`);
    res.json(result.rows);
  } catch (err) {
    console.error('Ошибка при получении продуктов:', err.message);
    res.status(500).json({ error: 'Database error', details: err.message });
  }
});

// POST new item
app.post('/api/items', async (req, res) => {
  try {
    const { name, isInFridge } = req.body;
    console.log('POST /api/items - добавление:', name);
    
    if (!name?.trim()) {
      return res.status(400).json({ error: 'Name is required' });
    }
    
    const result = await pool.query(
      'INSERT INTO fridge_items (name, is_in_fridge) VALUES ($1, $2) RETURNING *',
      [name.trim(), isInFridge ?? true]
    );
    
    console.log('Продукт добавлен:', result.rows[0].name);
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Ошибка при добавлении:', err.message);
    res.status(500).json({ error: 'Database error', details: err.message });
  }
});

// PATCH toggle item position
app.patch('/api/items/:id/toggle', async (req, res) => {
  try {
    const { id } = req.params;
    console.log(`PATCH /api/items/${id}/toggle - переключение позиции`);
    
    const result = await pool.query(
      'UPDATE fridge_items SET is_in_fridge = NOT is_in_fridge WHERE id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    console.log('✅ Позиция переключена:', result.rows[0].name);
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Ошибка при переключении:', err.message);
    res.status(500).json({ error: 'Database error', details: err.message });
  }
});

// DELETE item
app.delete('/api/items/:id', async (req, res) => {
  try {
    const { id } = req.params;
    console.log(`DELETE /api/items/${id} - удаление продукта`);
    
    const result = await pool.query('DELETE FROM fridge_items WHERE id = $1 RETURNING *', [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    console.log('Продукт удален:', result.rows[0].name);
    res.json({ message: 'Item deleted', deletedItem: result.rows[0] });
  } catch (err) {
    console.error('Ошибка при удалении:', err.message);
    res.status(500).json({ error: 'Database error', details: err.message });
  }
});

// Обработка несуществующих маршрутов
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Обработка глобальных ошибок
app.use((err, req, res, next) => {
  console.error('Глобальная ошибка:', err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// Запуск инициализации
initializeApp().catch(err => {
  console.error('Не удалось запустить приложение:', err);
  process.exit(1);
});