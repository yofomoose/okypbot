#!/bin/bash

echo "🔍 Проверка подключения к PostgreSQL в Docker"
echo "============================================="

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "🐘 Проверка PostgreSQL:"

# Простая проверка подключения
echo "1. Проверка версии PostgreSQL:"
docker exec okypbot_postgres psql -U postgres -c "SELECT version();"

echo ""
echo "2. Список баз данных:"
docker exec okypbot_postgres psql -U postgres -c "\l"

echo ""
echo "3. Проверка подключения к базе okypbot:"
docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"

echo ""
echo "4. Проверка таблиц в базе okypbot:"
docker exec okypbot_postgres psql -U postgres -d okypbot -c "\dt"

echo ""
echo "5. Тест простого запроса:"
docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'PostgreSQL работает!' as status;"

echo ""
echo "✅ Проверка завершена!"
