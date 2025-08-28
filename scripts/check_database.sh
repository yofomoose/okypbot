#!/bin/bash
# Скрипт для проверки и восстановления файловой базы данных пользователей

echo "🔍 Проверка файловой базы данных пользователей..."

# Проверяем, существует ли файл users.json
if [ ! -f "/app/database/users.json" ]; then
    echo "⚠️ Файл users.json не найден"

    # Ищем бэкапы в volumes
    BACKUP_DIR="/app/backups"
    if [ -d "$BACKUP_DIR" ]; then
        LATEST_BACKUP=$(find "$BACKUP_DIR" -name "users_*.json" -type f -printf '%T+ %p\n' 2>/dev/null | sort -r | head -n 1 | cut -d' ' -f2-)
        if [ -n "$LATEST_BACKUP" ]; then
            echo "📥 Восстановление из бэкапа: $LATEST_BACKUP"
            cp "$LATEST_BACKUP" "/app/database/users.json"
            echo "✅ Файловая база данных восстановлена"
        else
            echo "❌ Бэкапы не найдены, создаем пустую базу данных"
            mkdir -p /app/database
            echo "{}" > /app/database/users.json
        fi
    else
        echo "❌ Директория бэкапов не найдена, создаем пустую базу данных"
        mkdir -p /app/database
        echo "{}" > /app/database/users.json
    fi
else
    echo "✅ Файл users.json существует"
    USER_COUNT=$(jq '. | length' /app/database/users.json 2>/dev/null || echo "0")
    echo "👥 Количество пользователей: $USER_COUNT"
fi

# Проверяем файл user_issues.json
if [ ! -f "/app/database/user_issues.json" ]; then
    echo "⚠️ Файл user_issues.json не найден, создаем пустой"
    echo "{}" > /app/database/user_issues.json
else
    echo "✅ Файл user_issues.json существует"
fi

echo "🎯 Проверка завершена"</content>
<parameter name="filePath">c:\Users\YofoY\Documents\Что то долго хранимое\okypbot\scripts\check_database.sh
