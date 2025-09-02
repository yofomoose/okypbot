#!/bin/bash
set -e

echo "🔧 Инициализация PostgreSQL для okypbot"
echo "======================================"

# Устанавливаем пароль для пользователя postgres
echo "🔑 Устанавливаем пароль для пользователя postgres..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER USER postgres PASSWORD '$DB_PASSWORD';
EOSQL

echo "✅ Пароль установлен успешно"

# Создаем дополнительные настройки если нужно
echo "📋 Настройка завершена для базы данных: $POSTGRES_DB"
