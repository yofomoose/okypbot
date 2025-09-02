#!/bin/bash
# deploy_to_production.sh
# Скрипт для безопасного обновления контейнера с сохранением данных регистрации

# Настройки
CONTAINER_NAME="okypbot_app"
COMPOSE_FILE="docker/docker-compose.prod.yml"
BACKUP_DIR="database_backup"

echo "=== Безопасное обновление OkypBot в продакшене ==="
echo "Этот скрипт сохранит данные регистрации при пересборке контейнера"

# Шаг 1: Создаем директорию для резервных копий
mkdir -p $BACKUP_DIR

# Шаг 2: Проверяем, запущен ли контейнер
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ Контейнер $CONTAINER_NAME запущен, создаем резервную копию данных..."
    
    # Создаем резервную копию данных
    docker cp $CONTAINER_NAME:/app/database/users.json $BACKUP_DIR/users.json 2>/dev/null || echo "⚠️ Файл users.json не найден"
    docker cp $CONTAINER_NAME:/app/database/user_issues.json $BACKUP_DIR/user_issues.json 2>/dev/null || echo "⚠️ Файл user_issues.json не найден"
    docker cp $CONTAINER_NAME:/app/database/employee_mapping.json $BACKUP_DIR/employee_mapping.json 2>/dev/null || echo "⚠️ Файл employee_mapping.json не найден"
    
    echo "✅ Резервная копия создана в $BACKUP_DIR/"
else
    echo "⚠️ Контейнер $CONTAINER_NAME не запущен, пропускаем создание резервной копии"
fi

# Шаг 3: Останавливаем и удаляем контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose -f $COMPOSE_FILE down

# Шаг 4: Обновляем код из git (если нужно)
echo "📥 Обновляем код из репозитория..."
git pull

# Шаг 5: Пересобираем контейнеры
echo "🔄 Пересобираем контейнеры..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Шаг 6: Запускаем контейнеры
echo "▶️ Запускаем контейнеры..."
docker-compose -f $COMPOSE_FILE up -d

# Шаг 7: Ждем, пока контейнер полностью загрузится
echo "⏳ Ожидаем загрузки контейнера (10 секунд)..."
sleep 10

# Шаг 8: Восстанавливаем данные из резервной копии
echo "📤 Восстанавливаем данные из резервной копии..."

# Создаем директорию если она еще не существует
docker exec -i $CONTAINER_NAME mkdir -p /app/database

# Восстанавливаем файлы
if [ -f "$BACKUP_DIR/users.json" ]; then
    docker cp $BACKUP_DIR/users.json $CONTAINER_NAME:/app/database/users.json
    echo "✅ Восстановлен файл users.json"
fi

if [ -f "$BACKUP_DIR/user_issues.json" ]; then
    docker cp $BACKUP_DIR/user_issues.json $CONTAINER_NAME:/app/database/user_issues.json
    echo "✅ Восстановлен файл user_issues.json"
fi

if [ -f "$BACKUP_DIR/employee_mapping.json" ]; then
    docker cp $BACKUP_DIR/employee_mapping.json $CONTAINER_NAME:/app/database/employee_mapping.json
    echo "✅ Восстановлен файл employee_mapping.json"
fi

# Шаг 9: Исправляем права доступа на файлы
echo "🔑 Исправляем права доступа..."
docker exec -i $CONTAINER_NAME chmod 777 /app/database
docker exec -i $CONTAINER_NAME chmod 666 /app/database/*.json

# Шаг 10: Перезапускаем бот для применения изменений
echo "🔄 Перезапускаем контейнер для применения изменений..."
docker restart $CONTAINER_NAME

# Шаг 11: Проверяем статус
echo "📊 Статус контейнера:"
docker ps | grep $CONTAINER_NAME

echo "✅ Обновление завершено!"
echo "📋 Проверьте логи: docker logs $CONTAINER_NAME"
