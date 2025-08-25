-- Миграция для изменения типов колонок telegram_id на BIGINT

-- Изменение типа telegram_id в таблице users
ALTER TABLE users 
    ALTER COLUMN telegram_id TYPE BIGINT;

-- Изменение типа telegram_user_id в таблице usage_stats
ALTER TABLE usage_stats 
    ALTER COLUMN telegram_user_id TYPE BIGINT,
    ALTER COLUMN user_id TYPE BIGINT;

-- Изменение типа в таблице classifications
ALTER TABLE classifications 
    ALTER COLUMN user_id TYPE BIGINT,
    ALTER COLUMN telegram_user_id TYPE BIGINT,
    ALTER COLUMN created_by TYPE BIGINT;
