#!/bin/bash

echo "🔧 Исправление проблем с паролем PostgreSQL"
echo "==========================================="

# 1. Останавливаем приложение, но оставляем PostgreSQL
echo "🛑 Останавливаем приложение..."
docker stop okypbot_app 2>/dev/null || true

# 2. Подключаемся к PostgreSQL и исправляем пароль
echo "🔑 Исправляем пароль PostgreSQL..."

# Сброс пароля через Docker exec
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

echo "✅ Пароль обновлен"

# 3. Проверяем настройки аутентификации
echo "🔍 Проверяем настройки pg_hba.conf..."
docker exec okypbot_postgres cat /var/lib/postgresql/data/pg_hba.conf | grep -E "(local|host)" | tail -10

# 4. Перезагружаем конфигурацию PostgreSQL
echo "🔄 Перезагружаем конфигурацию PostgreSQL..."
docker exec okypbot_postgres psql -U postgres -c "SELECT pg_reload_conf();"

# 5. Проверяем подключение с паролем
echo "🧪 Тестируем подключение с паролем..."
export PGPASSWORD='Cnhjywsq97'
if docker exec -e PGPASSWORD='Cnhjywsq97' okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'Подключение с паролем работает!' as test;"; then
    echo "✅ Подключение с паролем работает"
else
    echo "❌ Подключение с паролем не работает"
    
    # Попробуем альтернативный способ
    echo "🔧 Пробуем альтернативный способ..."
    docker exec okypbot_postgres psql -U postgres <<EOF
\password postgres
Cnhjywsq97
Cnhjywsq97
EOF
fi

# 6. Создаем .env файл с правильными настройками
echo "📝 Создаем правильный .env файл..."
cat > .env << 'EOL'
# Telegram Bot Token
BOT_TOKEN=8461903171:AAFKNyFL5LcqFIHSaGePJZ-vCCNQU3kRIqA

# Okdesk API Token
OKDESK_API_TOKEN=4cf96e5bb33f06481e4aff5ff0a2aa740ce8490a

# Базовый URL вашего аккаунта Okdesk
OKDESK_BASE_URL=https://yapomogu55.okdesk.ru

# ID автора для комментариев
OKDESK_AUTHOR_ID=1

# PostgreSQL Configuration для Docker
DB_HOST=postgres
DB_PORT=5432
DB_NAME=okypbot
DB_USER=postgres
DB_PASSWORD=Cnhjywsq97

# Webhook настройки
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001

# Администраторы
ADMIN_IDS=413129274,398258337

# Debug
DEBUG=false
EOL

echo "✅ .env файл создан"

# 7. Пересобираем и запускаем приложение
echo "🔨 Пересобираем приложение..."
docker-compose build --no-cache okypbot

echo "🚀 Запускаем приложение..."
docker-compose up -d okypbot

# 8. Ждем запуска и проверяем логи
echo "⏳ Ждем запуска (10 секунд)..."
sleep 10

echo "📋 Проверяем логи приложения:"
docker logs okypbot_app --tail 20

echo ""
echo "📋 Последние логи PostgreSQL:"
docker logs okypbot_postgres --tail 10

echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "🎯 Результат:"
if docker logs okypbot_app 2>&1 | grep -q "password authentication failed"; then
    echo "❌ Все еще есть проблемы с паролем"
    echo "💡 Попробуйте полный перезапуск PostgreSQL:"
    echo "   docker-compose down"
    echo "   docker volume rm okypbot_postgres_data"
    echo "   docker-compose up -d"
else
    echo "✅ Проблемы с паролем устранены!"
fi
