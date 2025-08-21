#!/bin/bash

# Скрипт для обновления бота без пересборки БД

echo "🔄 Обновление бота..."

# Функция для определения команды docker compose
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "❌ Docker Compose не найден!"
        exit 1
    fi
}

DOCKER_COMPOSE=$(get_docker_compose_cmd)
echo "📦 Используется: $DOCKER_COMPOSE"

# Остановка только бота
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml stop bot

# Пересборка образа бота
echo "🔨 Пересборка образа бота..."
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml build bot

# Запуск бота
echo "🚀 Запуск обновленного бота..."
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml up -d bot

# Проверка статуса
echo "📊 Статус сервисов:"
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml ps

echo "✅ Обновление завершено!"

# Показать логи
echo "📝 Последние логи бота:"
docker-compose -f docker-compose.prod.yml logs --tail=20 bot
