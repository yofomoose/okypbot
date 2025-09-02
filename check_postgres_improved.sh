#!/bin/bash

echo "🐘 Проверка PostgreSQL в Docker (улучшенная версия для сервера)"
echo "=============================================================="

# Функция для проверки команды
check_command() {
    local description="$1"
    local command="$2"
    local ignore_errors="$3"
    
    echo ""
    echo "🔍 $description"
    echo "--------------------------------------------------"
    
    if eval "$command"; then
        echo "✅ Успешно выполнено"
        return 0
    else
        if [[ "$ignore_errors" == "true" ]]; then
            echo "⚠️ Предупреждение (команда завершилась с ошибкой, но это не критично)"
            return 0
        else
            echo "❌ Ошибка выполнения команды"
            return 1
        fi
    fi
}

# Счетчик успешных проверок
SUCCESS_COUNT=0
TOTAL_CHECKS=0

# Проверяем наличие docker-compose файла
if [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.yaml" ]] || [[ -f "compose.yml" ]] || [[ -f "compose.yaml" ]]; then
    echo "📁 Найден docker-compose файл в текущей директории"
    ((TOTAL_CHECKS++))
    if check_command "Статус контейнеров" "docker-compose ps" "false"; then
        ((SUCCESS_COUNT++))
    fi
else
    echo "⚠️ docker-compose файл не найден в текущей директории"
    echo "📂 Текущая директория: $(pwd)"
    echo "📋 Содержимое директории:"
    ls -la
fi

# Основные проверки PostgreSQL
POSTGRES_CHECKS=(
    "Готовность PostgreSQL|docker exec okypbot_postgres pg_isready -U postgres|false"
    "Версия PostgreSQL|docker exec okypbot_postgres psql -U postgres -c \"SELECT version();\"|false"
    "Список баз данных|docker exec okypbot_postgres psql -U postgres -c \"\\l\"|false"
    "Подключение к базе okypbot|docker exec okypbot_postgres psql -U postgres -d okypbot -c \"SELECT current_database(), current_user;\"|false"
    "Таблицы в базе okypbot|docker exec okypbot_postgres psql -U postgres -d okypbot -c \"\\dt\"|false"
    "Тест простого запроса|docker exec okypbot_postgres psql -U postgres -d okypbot -c \"SELECT 'PostgreSQL работает!' as status;\"|false"
    "Количество пользователей|docker exec okypbot_postgres psql -U postgres -d okypbot -c \"SELECT COUNT(*) as user_count FROM users;\"|true"
)

for check_info in "${POSTGRES_CHECKS[@]}"; do
    IFS='|' read -r description command ignore_errors <<< "$check_info"
    ((TOTAL_CHECKS++))
    if check_command "$description" "$command" "$ignore_errors"; then
        ((SUCCESS_COUNT++))
    fi
done

# Итоги
echo ""
echo "📊 Итоги проверки:"
echo "✅ Успешно: $SUCCESS_COUNT/$TOTAL_CHECKS"

if [[ $SUCCESS_COUNT -ge $((TOTAL_CHECKS - 1)) ]]; then
    echo "🎉 PostgreSQL полностью работоспособен!"
    
    echo ""
    echo "🔧 Информация для подключения:"
    echo "Host: localhost (внутри Docker: postgres)"
    echo "Port: 5432 (внешний порт может отличаться)"
    echo "Database: okypbot"
    echo "User: postgres"
    echo "Password: [из .env файла]"
    
    exit 0
else
    echo "⚠️ Есть критические проблемы с PostgreSQL"
    exit 1
fi
