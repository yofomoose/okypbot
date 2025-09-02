#!/usr/bin/env bash
# deploy_with_data_persistence.sh
# Скрипт для развертывания okypbot с сохранением пользовательских данных

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Развертывание OkypBot с сохранением данных ===${NC}"

# Проверка наличия файла с данными регистрации
BACKUP_DIR="./database_backup"
DATE=$(date '+%Y%m%d_%H%M%S')
DATA_DIR="/app/database"
CONTAINER_NAME="okypbot_app"

# Шаг 1: Создание резервной копии базы данных
echo -e "${YELLOW}[1/5] Создание резервной копии данных...${NC}"
mkdir -p "$BACKUP_DIR"

# Проверяем, запущен ли контейнер
if docker ps | grep -q $CONTAINER_NAME; then
    echo "Контейнер $CONTAINER_NAME запущен, создаем резервную копию данных..."
    
    # Копируем файлы из контейнера
    docker cp $CONTAINER_NAME:/app/database/users.json "$BACKUP_DIR/users_$DATE.json" 2>/dev/null || echo "Файл users.json не найден в контейнере"
    docker cp $CONTAINER_NAME:/app/database/user_issues.json "$BACKUP_DIR/user_issues_$DATE.json" 2>/dev/null || echo "Файл user_issues.json не найден в контейнере"
    docker cp $CONTAINER_NAME:/app/database/employee_mapping.json "$BACKUP_DIR/employee_mapping_$DATE.json" 2>/dev/null || echo "Файл employee_mapping.json не найден в контейнере"
    
    # Проверка успешности копирования
    if [ -f "$BACKUP_DIR/users_$DATE.json" ] || [ -f "$BACKUP_DIR/user_issues_$DATE.json" ]; then
        echo -e "${GREEN}✓ Резервная копия данных создана в $BACKUP_DIR${NC}"
    else
        echo -e "${YELLOW}! Предупреждение: Не удалось создать резервную копию данных, но продолжаем...${NC}"
    fi
else
    echo -e "${YELLOW}! Контейнер $CONTAINER_NAME не запущен, пропускаем создание резервной копии...${NC}"
fi

# Шаг 2: Остановка и удаление контейнеров
echo -e "${YELLOW}[2/5] Остановка контейнеров...${NC}"
cd docker
docker-compose -f docker-compose.prod.yml down
cd ..
echo -e "${GREEN}✓ Контейнеры остановлены${NC}"

# Шаг 3: Сборка новых образов
echo -e "${YELLOW}[3/5] Сборка новых Docker-образов...${NC}"
cd docker
docker-compose -f docker-compose.prod.yml build --no-cache
cd ..
echo -e "${GREEN}✓ Образы собраны${NC}"

# Шаг 4: Запуск контейнеров
echo -e "${YELLOW}[4/5] Запуск контейнеров...${NC}"
cd docker
docker-compose -f docker-compose.prod.yml up -d
cd ..
echo -e "${GREEN}✓ Контейнеры запущены${NC}"

# Шаг 5: Восстановление данных
echo -e "${YELLOW}[5/5] Восстановление данных регистрации...${NC}"
sleep 10 # Даем контейнерам время на запуск

# Находим последние резервные копии
LATEST_USERS=$(ls -t "$BACKUP_DIR"/users_*.json 2>/dev/null | head -1)
LATEST_ISSUES=$(ls -t "$BACKUP_DIR"/user_issues_*.json 2>/dev/null | head -1)
LATEST_MAPPING=$(ls -t "$BACKUP_DIR"/employee_mapping_*.json 2>/dev/null | head -1)

# Проверяем наличие файлов для восстановления
if [ -n "$LATEST_USERS" ] || [ -n "$LATEST_ISSUES" ] || [ -n "$LATEST_MAPPING" ]; then
    # Создаем директорию в контейнере если она еще не существует
    docker exec -i $CONTAINER_NAME mkdir -p /app/database
    
    # Восстанавливаем данные
    if [ -n "$LATEST_USERS" ]; then
        docker cp "$LATEST_USERS" $CONTAINER_NAME:/app/database/users.json
        echo -e "${GREEN}✓ Данные пользователей восстановлены из $LATEST_USERS${NC}"
    fi
    
    if [ -n "$LATEST_ISSUES" ]; then
        docker cp "$LATEST_ISSUES" $CONTAINER_NAME:/app/database/user_issues.json
        echo -e "${GREEN}✓ Данные заявок восстановлены из $LATEST_ISSUES${NC}"
    fi
    
    if [ -n "$LATEST_MAPPING" ]; then
        docker cp "$LATEST_MAPPING" $CONTAINER_NAME:/app/database/employee_mapping.json
        echo -e "${GREEN}✓ Данные сопоставлений восстановлены из $LATEST_MAPPING${NC}"
    fi
    
    # Исправляем права доступа
    docker exec -i $CONTAINER_NAME chmod 777 /app/database
    docker exec -i $CONTAINER_NAME chmod 666 /app/database/*.json
    
    # Перезапускаем бота для применения изменений
    docker restart $CONTAINER_NAME
    echo -e "${GREEN}✓ Бот перезапущен с восстановленными данными${NC}"
else
    echo -e "${YELLOW}! Резервных копий не найдено, пропускаем восстановление...${NC}"
fi

# Проверяем статус контейнеров
echo -e "${YELLOW}Проверка статуса контейнеров:${NC}"
docker ps | grep okypbot

echo -e "${GREEN}=== Развертывание завершено ===${NC}"
echo "Проверьте работу бота и веб-хука"
