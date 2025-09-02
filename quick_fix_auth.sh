#!/bin/bash

echo "⚡ Быстрое исправление аутентификации PostgreSQL"
echo "=============================================="

echo "🔑 Устанавливаем пароль для postgres..."
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

echo "🔧 Обновляем pg_hba.conf для использования md5..."
docker exec okypbot_postgres bash -c "echo 'host all all all md5' >> /var/lib/postgresql/data/pgdata/pg_hba.conf"

echo "🔄 Перезагружаем конфигурацию PostgreSQL..."
docker exec okypbot_postgres psql -U postgres -c "SELECT pg_reload_conf();"

echo "⏳ Ждем 5 секунд..."
sleep 5

echo "🔍 Тестируем подключение с паролем..."
PGPASSWORD=Cnhjywsq97 docker exec okypbot_postgres psql -U postgres -d okypbot -h localhost -c "SELECT 'Аутентификация работает!' as result;"

echo "🚀 Перезапускаем приложение..."
docker restart okypbot_app

echo "⏳ Ждем запуска приложения..."
sleep 10

echo "📋 Проверяем логи приложения..."
docker logs okypbot_app | tail -5

echo ""
echo "✅ Исправление завершено!"
echo "🌐 Теперь приложение должно подключаться к PostgreSQL"
