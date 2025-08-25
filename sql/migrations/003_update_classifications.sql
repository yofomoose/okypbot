-- Миграция для обновления классификаций и установки значений по умолчанию

-- Обновляем таблицу классификаций
ALTER TABLE classifications
    ALTER COLUMN confidence SET DEFAULT 0.0;

-- Удаляем старые неиспользуемые колонки
ALTER TABLE classifications 
    DROP COLUMN IF EXISTS predicted_category,
    DROP COLUMN IF EXISTS user_id,
    DROP COLUMN IF EXISTS telegram_user_id,
    DROP COLUMN IF EXISTS model_version;

-- Переименовываем и устанавливаем правильные настройки
ALTER TABLE classifications 
    ALTER COLUMN text TYPE TEXT,
    ALTER COLUMN category TYPE TEXT,
    ALTER COLUMN confidence TYPE REAL,
    ALTER COLUMN created_by TYPE BIGINT;
