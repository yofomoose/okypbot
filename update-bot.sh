#!/bin/bash

# Проверка наличия изменений
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "✅ Бот уже обновлен до последней версии"
    exit 0
fi

# Создание резервной копии базы
echo "📦 Создание резервной копии базы..."
docker compose -f docker/docker-compose.prod.yml exec -T postgres pg_dump -U postgres okypbot > backup_$(date +%Y%m%d_%H%M%S).sql

# Получение обновлений
echo "⬇️ Получение обновлений..."
git pull

# Проверка изменений в requirements.txt
if git diff HEAD~ --name-only | grep -q "requirements.txt"; then
    echo "📚 Обнаружены изменения в requirements.txt, выполняем полную пересборку..."
    docker compose -f docker/docker-compose.prod.yml build --no-cache
else
    echo "🔄 Обычная пересборка..."
    docker compose -f docker/docker-compose.prod.yml build
fi

# Перезапуск контейнеров
echo "🚀 Перезапуск контейнеров..."
docker compose -f docker/docker-compose.prod.yml up -d

# Проверка логов на ошибки
echo "📋 Проверка логов..."
docker compose -f docker/docker-compose.prod.yml logs --tail=50

echo "✅ Обновление завершено"
