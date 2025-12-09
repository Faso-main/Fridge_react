-- Создание таблицы если она не существует
CREATE TABLE IF NOT EXISTS fridge_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_in_fridge BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка тестовых данных (опционально)
INSERT INTO fridge_items (name, is_in_fridge) 
VALUES 
    ('Молоко', true),
    ('Яйца', true),
    ('Хлеб', false),
    ('Сыр', true),
    ('Помидоры', true),
    ('Курица', true)
ON CONFLICT DO NOTHING;

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_fridge_items_name ON fridge_items(name);
CREATE INDEX IF NOT EXISTS idx_fridge_items_status ON fridge_items(is_in_fridge);