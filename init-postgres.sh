#!/bin/bash
set -e

echo "🔧 Инициализация PostgreSQL для okypbot"
echo "======================================"

# Устанавливаем пароль для пользователя postgres
echo "🔑 Устанавливаем пароль для пользователя postgres..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER USER postgres PASSWORD 'Cnhjywsq97';
EOSQL

echo "✅ Пароль установлен успешно"

# Обновляем pg_hba.conf для md5 аутентификации
echo "🔧 Настройка аутентификации..."
echo "host all all all md5" >> /var/lib/postgresql/data/pgdata/pg_hba.conf

echo "📋 Настройка завершена для базы данных: $POSTGRES_DB"
