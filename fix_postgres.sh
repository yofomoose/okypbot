#!/bin/bash
# Скрипт для исправления проблем с PostgreSQL в Docker

echo "🔧 Исправление проблем с PostgreSQL"
echo "=================================="

# 1. Останавливаем все контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose down

# 2. Очищаем volumes (опционально - удалит данные!)
echo "🗑️ Очищаем volumes PostgreSQL..."
docker volume rm okypbot_postgres_data 2>/dev/null || true

# 3. Пересобираем образы
echo "🔨 Пересобираем образы..."
docker-compose build --no-cache

# 4. Запускаем PostgreSQL первым
echo "🐘 Запускаем PostgreSQL..."
docker-compose up -d postgres

# Ждем запуска PostgreSQL
echo "⏳ Ждем запуска PostgreSQL (30 секунд)..."
sleep 30

# 5. Создаем базу данных и пользователя
echo "📋 Настраиваем базу данных..."
docker exec okypbot_postgres psql -U postgres -c "CREATE DATABASE okypbot;" 2>/dev/null || echo "База данных уже существует"
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

# 6. Проверяем подключение
echo "🔍 Проверяем подключение..."
docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL настроен правильно!"
    
    # 7. Запускаем основное приложение
    echo "🚀 Запускаем основное приложение..."
    docker-compose up -d
    
    echo "📊 Статус контейнеров:"
    docker-compose ps
    
    echo ""
    echo "🎉 Настройка завершена!"
    echo "📝 Логи можно посмотреть командой: docker-compose logs -f"
    echo "🌐 Webhook доступен на: http://localhost:8001/okdesk-webhook"
    
else
    echo "❌ Ошибка настройки PostgreSQL"
    echo "📋 Логи PostgreSQL:"
    docker-compose logs postgres
fi
