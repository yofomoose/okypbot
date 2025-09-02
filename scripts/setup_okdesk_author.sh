#!/bin/bash
# Скрипт для конфигурации ID автора комментариев в OkDesk

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Сброс цвета

echo -e "${BLUE}=== Настройка Author ID для OkDesk ===${NC}"

# Проверяем, существует ли контейнер okypbot_app
if ! docker ps -a | grep -q okypbot_app; then
    echo -e "${RED}❌ Контейнер okypbot_app не найден!${NC}"
    exit 1
fi

# Получаем текущее значение из переменных окружения
CURRENT_AUTHOR_ID=$(docker exec -it okypbot_app bash -c 'echo $OKDESK_AUTHOR_ID')

echo -e "${YELLOW}Текущий ID автора для комментариев: ${CURRENT_AUTHOR_ID:-не установлен}${NC}"

# Запрашиваем новое значение у пользователя
echo -e "${BLUE}Введите ID автора для комментариев в OkDesk (обычно это ID сотрудника):${NC}"
read -p "> " NEW_AUTHOR_ID

if [ -z "$NEW_AUTHOR_ID" ]; then
    echo -e "${RED}ID не может быть пустым!${NC}"
    exit 1
fi

# Проверяем, что введенное значение - число
if ! [[ "$NEW_AUTHOR_ID" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}ID должен быть целым числом!${NC}"
    exit 1
fi

echo -e "${YELLOW}Устанавливаем ID автора: $NEW_AUTHOR_ID${NC}"

# Создаем или обновляем файл конфигурации
CONFIG_FILE="config/okdesk_config.py"

# Проверяем существование директории config
if [ ! -d "config" ]; then
    echo -e "${YELLOW}Создаем директорию config${NC}"
    mkdir -p config
fi

# Создаем файл конфигурации
cat > $CONFIG_FILE << EOF
"""
Дополнительные настройки для OkDesk API
"""

# ID автора для комментариев (обычно ID сотрудника)
OKDESK_AUTHOR_ID = $NEW_AUTHOR_ID
EOF

echo -e "${GREEN}✅ Файл конфигурации создан: $CONFIG_FILE${NC}"

# Обновляем __init__.py в директории config, чтобы добавить импорт
INIT_FILE="config/__init__.py"

# Проверяем существование файла
if [ ! -f "$INIT_FILE" ]; then
    echo -e "${YELLOW}Создаем файл $INIT_FILE${NC}"
    touch "$INIT_FILE"
fi

# Проверяем, есть ли уже импорт
if grep -q "okdesk_config import OKDESK_AUTHOR_ID" "$INIT_FILE"; then
    echo -e "${YELLOW}Импорт OKDESK_AUTHOR_ID уже добавлен в $INIT_FILE${NC}"
else
    # Добавляем импорт
    echo "# Импортируем настройки OkDesk" >> "$INIT_FILE"
    echo "try:" >> "$INIT_FILE"
    echo "    from .okdesk_config import OKDESK_AUTHOR_ID" >> "$INIT_FILE"
    echo "except ImportError:" >> "$INIT_FILE"
    echo "    OKDESK_AUTHOR_ID = None" >> "$INIT_FILE"
    echo -e "${GREEN}✅ Импорт OKDESK_AUTHOR_ID добавлен в $INIT_FILE${NC}"
fi

# Обновляем переменную окружения в контейнере
echo -e "${YELLOW}Обновляем переменную окружения в контейнере...${NC}"
docker exec -it okypbot_app bash -c "export OKDESK_AUTHOR_ID=$NEW_AUTHOR_ID"

echo -e "${GREEN}✅ Переменная окружения OKDESK_AUTHOR_ID установлена в контейнере${NC}"

# Рекомендации для перезапуска
echo -e "${BLUE}Для применения изменений рекомендуется перезапустить контейнер:${NC}"
echo -e "${YELLOW}docker-compose -f docker/docker-compose.prod.yml restart bot${NC}"

echo -e "${GREEN}=== Настройка завершена! ===${NC}"
