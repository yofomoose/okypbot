#!/bin/bash

# Скрипт для обновления бота без пересборки БД

echo "🔄 Обновление бота..."

# Остановка только бота
docker-compose -f docker-compose.prod.yml stop bot

# Пересборка образа бота
echo "🔨 Пересборка образа бота..."
docker-compose -f docker-compose.prod.yml build bot

# Запуск бота
echo "🚀 Запуск обновленного бота..."
docker-compose -f docker-compose.prod.yml up -d bot

# Проверка статуса
echo "📊 Статус сервисов:"
docker-compose -f docker-compose.prod.yml ps

echo "✅ Обновление завершено!"

# Показать логи
echo "📝 Последние логи бота:"
docker-compose -f docker-compose.prod.yml logs --tail=20 bot
