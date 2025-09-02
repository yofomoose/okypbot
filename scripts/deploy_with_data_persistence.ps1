# Скрипт для развертывания OkypBot с сохранением пользовательских данных

# Цвета для вывода (не работают в стандартной PowerShell, но сохраним для Windows Terminal)
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Развертывание OkypBot с сохранением данных ===${NC}"

# Проверка наличия файла с данными регистрации
$BACKUP_DIR = "./database_backup"
$DATE = Get-Date -Format "yyyyMMdd_HHmmss"
$DATA_DIR = "/app/database"
$CONTAINER_NAME = "okypbot_app"

# Шаг 1: Создание резервной копии базы данных
Write-Host "${YELLOW}[1/5] Создание резервной копии данных...${NC}"
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
}

# Проверяем, запущен ли контейнер
$containerRunning = docker ps | Select-String -Pattern $CONTAINER_NAME
if ($containerRunning) {
    Write-Host "Контейнер $CONTAINER_NAME запущен, создаем резервную копию данных..."
    
    # Копируем файлы из контейнера
    docker cp ${CONTAINER_NAME}:/app/database/users.json "$BACKUP_DIR/users_$DATE.json" 2>$null
    if (-not $?) { Write-Host "Файл users.json не найден в контейнере" }
    
    docker cp ${CONTAINER_NAME}:/app/database/user_issues.json "$BACKUP_DIR/user_issues_$DATE.json" 2>$null
    if (-not $?) { Write-Host "Файл user_issues.json не найден в контейнере" }
    
    docker cp ${CONTAINER_NAME}:/app/database/employee_mapping.json "$BACKUP_DIR/employee_mapping_$DATE.json" 2>$null
    if (-not $?) { Write-Host "Файл employee_mapping.json не найден в контейнере" }
    
    # Проверка успешности копирования
    if ((Test-Path "$BACKUP_DIR/users_$DATE.json") -or (Test-Path "$BACKUP_DIR/user_issues_$DATE.json")) {
        Write-Host "${GREEN}✓ Резервная копия данных создана в $BACKUP_DIR${NC}"
    } else {
        Write-Host "${YELLOW}! Предупреждение: Не удалось создать резервную копию данных, но продолжаем...${NC}"
    }
} else {
    Write-Host "${YELLOW}! Контейнер $CONTAINER_NAME не запущен, пропускаем создание резервной копии...${NC}"
}

# Шаг 2: Остановка и удаление контейнеров
Write-Host "${YELLOW}[2/5] Остановка контейнеров...${NC}"
Push-Location docker
docker-compose -f docker-compose.prod.yml down
Pop-Location
Write-Host "${GREEN}✓ Контейнеры остановлены${NC}"

# Шаг 3: Сборка новых образов
Write-Host "${YELLOW}[3/5] Сборка новых Docker-образов...${NC}"
Push-Location docker
docker-compose -f docker-compose.prod.yml build --no-cache
Pop-Location
Write-Host "${GREEN}✓ Образы собраны${NC}"

# Шаг 4: Запуск контейнеров
Write-Host "${YELLOW}[4/5] Запуск контейнеров...${NC}"
Push-Location docker
docker-compose -f docker-compose.prod.yml up -d
Pop-Location
Write-Host "${GREEN}✓ Контейнеры запущены${NC}"

# Шаг 5: Восстановление данных
Write-Host "${YELLOW}[5/5] Восстановление данных регистрации...${NC}"
Start-Sleep -Seconds 10 # Даем контейнерам время на запуск

# Находим последние резервные копии
$LATEST_USERS = Get-ChildItem "$BACKUP_DIR/users_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$LATEST_ISSUES = Get-ChildItem "$BACKUP_DIR/user_issues_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$LATEST_MAPPING = Get-ChildItem "$BACKUP_DIR/employee_mapping_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Проверяем наличие файлов для восстановления
if ($LATEST_USERS -or $LATEST_ISSUES -or $LATEST_MAPPING) {
    # Создаем директорию в контейнере если она еще не существует
    docker exec -i $CONTAINER_NAME mkdir -p /app/database
    
    # Восстанавливаем данные
    if ($LATEST_USERS) {
        docker cp $LATEST_USERS.FullName "${CONTAINER_NAME}:/app/database/users.json"
        Write-Host "${GREEN}✓ Данные пользователей восстановлены из $($LATEST_USERS.Name)${NC}"
    }
    
    if ($LATEST_ISSUES) {
        docker cp $LATEST_ISSUES.FullName "${CONTAINER_NAME}:/app/database/user_issues.json"
        Write-Host "${GREEN}✓ Данные заявок восстановлены из $($LATEST_ISSUES.Name)${NC}"
    }
    
    if ($LATEST_MAPPING) {
        docker cp $LATEST_MAPPING.FullName "${CONTAINER_NAME}:/app/database/employee_mapping.json"
        Write-Host "${GREEN}✓ Данные сопоставлений восстановлены из $($LATEST_MAPPING.Name)${NC}"
    }
    
    # Исправляем права доступа
    docker exec -i $CONTAINER_NAME chmod 777 /app/database
    docker exec -i $CONTAINER_NAME chmod 666 /app/database/*.json
    
    # Перезапускаем бота для применения изменений
    docker restart $CONTAINER_NAME
    Write-Host "${GREEN}✓ Бот перезапущен с восстановленными данными${NC}"
} else {
    Write-Host "${YELLOW}! Резервных копий не найдено, пропускаем восстановление...${NC}"
}

# Проверяем статус контейнеров
Write-Host "${YELLOW}Проверка статуса контейнеров:${NC}"
docker ps | Select-String -Pattern "okypbot"

Write-Host "${GREEN}=== Развертывание завершено ===${NC}"
Write-Host "Проверьте работу бота и веб-хука"
