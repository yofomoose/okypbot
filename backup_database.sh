#!/bin/bash
# backup_database.sh
# Скрипт для создания резервных копий файлов базы данных из контейнера

# Настройки
CONTAINER_NAME="okypbot_app"
BACKUP_DIR="database_backup/$(date +%Y%m%d_%H%M)"

# Создаем директорию с датой и временем
mkdir -p $BACKUP_DIR

echo "=== Создание резервной копии базы данных ==="
echo "$(date) - Начало резервного копирования"

# Копируем файлы из контейнера
docker cp $CONTAINER_NAME:/app/database/users.json $BACKUP_DIR/users.json 2>/dev/null || echo "⚠️ Файл users.json не найден"
docker cp $CONTAINER_NAME:/app/database/user_issues.json $BACKUP_DIR/user_issues.json 2>/dev/null || echo "⚠️ Файл user_issues.json не найден"
docker cp $CONTAINER_NAME:/app/database/employee_mapping.json $BACKUP_DIR/employee_mapping.json 2>/dev/null || echo "⚠️ Файл employee_mapping.json не найден"

# Подсчитываем количество файлов
FILE_COUNT=$(find $BACKUP_DIR -type f | wc -l)

echo "✅ Резервная копия создана в $BACKUP_DIR"
echo "📊 Скопировано файлов: $FILE_COUNT"
echo "$(date) - Резервное копирование завершено"

# Оставляем только 10 последних резервных копий
if [ $(find database_backup -mindepth 1 -maxdepth 1 -type d | wc -l) -gt 10 ]; then
    echo "🧹 Удаляем старые резервные копии..."
    ls -t -1 database_backup | tail -n +11 | xargs -I {} rm -rf database_backup/{}
fi
