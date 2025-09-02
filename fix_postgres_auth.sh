#!/bin/bash

echo "🔧 Исправление аутентификации PostgreSQL"
echo "========================================"

# Устанавливаем пароль для пользователя postgres
echo "🔑 Устанавливаем пароль для пользователя postgres..."
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

if [ $? -eq 0 ]; then
    echo "✅ Пароль успешно установлен"
else
    echo "❌ Ошибка установки пароля"
    exit 1
fi

# Проверяем подключение с паролем
echo ""
echo "🔍 Проверяем подключение с паролем..."
PGPASSWORD=Cnhjywsq97 docker exec okypbot_postgres psql -U postgres -d okypbot -h localhost -c "SELECT 'Подключение с паролем работает!' as status;"

if [ $? -eq 0 ]; then
    echo "✅ Подключение с паролем работает!"
else
    echo "❌ Подключение с паролем не работает"
    
    # Пытаемся обновить pg_hba.conf для использования md5 вместо scram-sha-256
    echo "🔧 Обновляем настройки аутентификации..."
    docker exec okypbot_postgres sed -i 's/scram-sha-256/md5/g' /var/lib/postgresql/data/pgdata/pg_hba.conf
    
    # Перезагружаем конфигурацию
    docker exec okypbot_postgres psql -U postgres -c "SELECT pg_reload_conf();"
    
    echo "⏳ Ждем применения настроек..."
    sleep 5
    
    # Проверяем снова
    PGPASSWORD=Cnhjywsq97 docker exec okypbot_postgres psql -U postgres -d okypbot -h localhost -c "SELECT 'Подключение после настройки работает!' as status;"
fi

echo ""
echo "📊 Проверяем логи приложения..."
docker logs okypbot_app | tail -10

echo ""
echo "✅ Исправление завершено!"
