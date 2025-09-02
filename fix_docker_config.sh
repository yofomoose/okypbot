#!/bin/bash

echo "🔧 Исправление конфигурации Docker и перезапуск"
echo "=============================================="

# Останавливаем контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose down

# Очищаем старые образы
echo "🧹 Очищаем старые образы..."
docker system prune -f

# Пересобираем с новой конфигурацией  
echo "🔨 Пересобираем приложение..."
docker-compose build --no-cache

# Запускаем заново
echo "🚀 Запускаем с исправленной конфигурацией..."
docker-compose --env-file .env.production up -d

# Ждем запуска
echo "⏳ Ждем запуска контейнеров..."
sleep 15

# Проверяем статус
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "📋 Логи PostgreSQL:"
docker-compose logs postgres | tail -10

echo ""
echo "📋 Логи приложения:"
docker-compose logs okypbot | tail -10

echo ""
echo "🔍 Проверка подключения к PostgreSQL..."
docker exec okypbot_postgres pg_isready -U postgres

echo ""
echo "✅ Перезапуск завершен!"
echo "🌐 Webhook доступен на: http://localhost:8080/okdesk-webhook"
