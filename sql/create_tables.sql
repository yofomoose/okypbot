-- Создание таблиц для okypbot
-- Этот скрипт можно выполнить вручную или через init_database()

-- Таблица для результатов классификации
CREATE TABLE IF NOT EXISTS classifications (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    predicted_category VARCHAR(255) NOT NULL,
    confidence REAL,
    user_id INTEGER,
    telegram_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Поля для обратной связи
    is_correct BOOLEAN,
    correct_category VARCHAR(255),
    feedback_at TIMESTAMP,
    is_training BOOLEAN DEFAULT FALSE,
    
    -- Техническая информация
    model_version VARCHAR(100),
    processing_time REAL
);

-- Таблица для статистики использования
CREATE TABLE IF NOT EXISTS usage_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processing_time REAL,
    success BOOLEAN DEFAULT TRUE
);

-- Таблица для статистики моделей
CREATE TABLE IF NOT EXISTS model_stats (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(100) NOT NULL,
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category_stats JSONB
);

-- Таблица для обратной связи пользователей
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    classification_id INTEGER REFERENCES classifications(id),
    user_id INTEGER NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    is_prediction_correct BOOLEAN,
    suggested_category VARCHAR(255),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_classifications_user_id ON classifications(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_classifications_created_at ON classifications(created_at);
CREATE INDEX IF NOT EXISTS idx_classifications_category ON classifications(predicted_category);
CREATE INDEX IF NOT EXISTS idx_classifications_feedback ON classifications(is_correct) WHERE is_correct IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_usage_stats_user_id ON usage_stats(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_usage_stats_timestamp ON usage_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_stats_action ON usage_stats(action_type);

CREATE INDEX IF NOT EXISTS idx_feedback_classification ON user_feedback(classification_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON user_feedback(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_processed ON user_feedback(processed);

-- Комментарии к таблицам
COMMENT ON TABLE classifications IS 'Результаты ML классификации заявок';
COMMENT ON TABLE usage_stats IS 'Статистика использования ML сервиса';
COMMENT ON TABLE model_stats IS 'Статистика точности ML моделей';
COMMENT ON TABLE user_feedback IS 'Обратная связь пользователей по классификации';

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_model_stats_updated_at 
    BEFORE UPDATE ON model_stats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Проверка созданных таблиц
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('classifications', 'usage_stats', 'model_stats', 'user_feedback')
ORDER BY table_name;
