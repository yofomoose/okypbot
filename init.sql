-- Инициализация базы данных OkypBot
-- Этот файл выполняется автоматически при первом запуске PostgreSQL

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE okypbot'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'okypbot')\gexec

\c okypbot

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    user_type VARCHAR(20) CHECK (user_type IN ('individual', 'legal')),
    position VARCHAR(100), -- для юридических лиц
    inn VARCHAR(12), -- ИНН компании для юридических лиц
    okdesk_contact_id INTEGER,
    okdesk_company_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    registration_completed BOOLEAN DEFAULT FALSE
);

-- Таблица заявок
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    okdesk_issue_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(20),
    issue_type VARCHAR(100),
    ml_category VARCHAR(100), -- ML классификация
    ml_confidence FLOAT, -- уверенность ML модели (0-1)
    assignee_id INTEGER, -- ID исполнителя в Okdesk
    assignee_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Таблица комментариев
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    okdesk_comment_id INTEGER UNIQUE NOT NULL,
    issue_id INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    author_type VARCHAR(20), -- 'client' или 'employee'
    author_id INTEGER,
    author_name VARCHAR(200),
    content TEXT NOT NULL,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов ML классификации
CREATE TABLE IF NOT EXISTS ml_predictions (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    predicted_category VARCHAR(100),
    confidence FLOAT,
    model_version VARCHAR(20),
    processing_time_ms INTEGER, -- время обработки в миллисекундах
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица настроек системы
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов webhook событий
CREATE TABLE IF NOT EXISTS webhook_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_okdesk_contact_id ON users(okdesk_contact_id);
CREATE INDEX IF NOT EXISTS idx_issues_okdesk_issue_id ON issues(okdesk_issue_id);
CREATE INDEX IF NOT EXISTS idx_issues_user_id ON issues(user_id);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues(created_at);
CREATE INDEX IF NOT EXISTS idx_comments_issue_id ON comments(issue_id);
CREATE INDEX IF NOT EXISTS idx_comments_okdesk_comment_id ON comments(okdesk_comment_id);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_issue_id ON ml_predictions(issue_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event_type ON webhook_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_created_at ON webhook_logs(created_at);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_issues_updated_at BEFORE UPDATE ON issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Вставка начальных настроек
INSERT INTO system_settings (key, value, description) VALUES
    ('ml_model_version', '1.0.0', 'Версия ML модели классификации'),
    ('ml_confidence_threshold', '0.7', 'Минимальный порог уверенности ML модели'),
    ('webhook_secret_configured', 'false', 'Настроен ли webhook secret'),
    ('bot_initialized', 'true', 'Флаг инициализации бота')
ON CONFLICT (key) DO NOTHING;

-- Создание представлений для удобства
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.telegram_id,
    u.first_name,
    u.last_name,
    u.user_type,
    COUNT(i.id) as total_issues,
    COUNT(CASE WHEN i.status = 'opened' THEN 1 END) as open_issues,
    COUNT(CASE WHEN i.status = 'closed' THEN 1 END) as closed_issues,
    MAX(i.created_at) as last_issue_date
FROM users u
LEFT JOIN issues i ON u.id = i.user_id
GROUP BY u.id, u.telegram_id, u.first_name, u.last_name, u.user_type;

-- Представление для статистики ML классификации
CREATE OR REPLACE VIEW ml_stats AS
SELECT 
    predicted_category,
    COUNT(*) as predictions_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence,
    AVG(processing_time_ms) as avg_processing_time
FROM ml_predictions
GROUP BY predicted_category
ORDER BY predictions_count DESC;

-- Функция для очистки старых логов
CREATE OR REPLACE FUNCTION cleanup_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Права доступа
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Настройка для удаленного подключения
ALTER SYSTEM SET listen_addresses = '*';
ALTER SYSTEM SET max_connections = 100;

-- Логирование
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';

SELECT pg_reload_conf();

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Зарегистрированные пользователи бота';
COMMENT ON TABLE issues IS 'Заявки пользователей в Okdesk';
COMMENT ON TABLE comments IS 'Комментарии к заявкам';
COMMENT ON TABLE ml_predictions IS 'Логи ML классификации заявок';
COMMENT ON TABLE system_settings IS 'Настройки системы';
COMMENT ON TABLE webhook_logs IS 'Логи обработки webhook событий';

COMMENT ON COLUMN users.telegram_id IS 'Уникальный ID пользователя в Telegram';
COMMENT ON COLUMN users.user_type IS 'Тип пользователя: individual (физ. лицо) или legal (юр. лицо)';
COMMENT ON COLUMN issues.ml_category IS 'Категория, определенная ML моделью';
COMMENT ON COLUMN issues.ml_confidence IS 'Уверенность ML модели в классификации (0-1)';

-- Вывод информации об инициализации
DO $$
BEGIN
    RAISE NOTICE 'База данных OkypBot успешно инициализирована!';
    RAISE NOTICE 'Создано таблиц: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE');
    RAISE NOTICE 'Создано индексов: %', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE 'Создано представлений: %', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public');
END $$;
