# Скрипт для восстановления данных регистрации в контейнер Docker
# Restore-RegistrationData.ps1

param (
    [string]$ContainerName = "okypbot_app",
    [string]$BackupDir = "database_backup",
    [switch]$RestartContainer = $true,
    [int]$WaitSeconds = 5
)

# Импортируем вспомогательные функции
Import-Module "$PSScriptRoot\PersistenceHelpers.psm1" -Force -ErrorAction SilentlyContinue

# Вывод информации
Write-Host "📥 Восстановление данных регистрации..." -ForegroundColor Cyan

# Проверяем, существует ли директория с резервными копиями
if (-not (Test-Path $BackupDir)) {
    Write-Host "❌ Директория с резервными копиями не найдена: $BackupDir" -ForegroundColor Red
    exit 1
}

# Проверяем, запущен ли контейнер
$containerRunning = docker ps | Select-String -Pattern $ContainerName
if ($null -eq $containerRunning) {
    Write-Host "⚠️ Контейнер $ContainerName не запущен, восстановление невозможно" -ForegroundColor Yellow
    exit 1
}

# Находим последние резервные копии
$latestUsers = Get-ChildItem "$BackupDir/users_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestIssues = Get-ChildItem "$BackupDir/user_issues_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestMapping = Get-ChildItem "$BackupDir/employee_mapping_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Проверяем наличие файлов для восстановления
$filesRestored = 0

# Создаем директорию в контейнере если она еще не существует
docker exec -i $ContainerName mkdir -p /app/database 2>$null

# Восстанавливаем данные пользователей
if ($null -ne $latestUsers) {
    docker cp $latestUsers.FullName "${ContainerName}:/app/database/users.json"
    if ($?) {
        Write-Host "✓ Данные пользователей восстановлены из $($latestUsers.Name)" -ForegroundColor Green
        $filesRestored++
    } else {
        Write-Host "❌ Ошибка при восстановлении данных пользователей" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️ Файл с данными пользователей не найден" -ForegroundColor Blue
}

# Восстанавливаем данные заявок
if ($null -ne $latestIssues) {
    docker cp $latestIssues.FullName "${ContainerName}:/app/database/user_issues.json"
    if ($?) {
        Write-Host "✓ Данные заявок восстановлены из $($latestIssues.Name)" -ForegroundColor Green
        $filesRestored++
    } else {
        Write-Host "❌ Ошибка при восстановлении данных заявок" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️ Файл с данными заявок не найден" -ForegroundColor Blue
}

# Восстанавливаем данные сопоставлений
if ($null -ne $latestMapping) {
    docker cp $latestMapping.FullName "${ContainerName}:/app/database/employee_mapping.json"
    if ($?) {
        Write-Host "✓ Данные сопоставлений восстановлены из $($latestMapping.Name)" -ForegroundColor Green
        $filesRestored++
    } else {
        Write-Host "❌ Ошибка при восстановлении данных сопоставлений" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️ Файл с данными сопоставлений не найден" -ForegroundColor Blue
}

# Исправляем права доступа
if ($filesRestored -gt 0) {
    docker exec -i $ContainerName chmod 777 /app/database 2>$null
    docker exec -i $ContainerName chmod 666 /app/database/*.json 2>$null
    Write-Host "✓ Права доступа к файлам исправлены" -ForegroundColor Green
    
    # Перезапускаем контейнер для применения изменений
    if ($RestartContainer) {
        Write-Host "🔄 Перезапуск контейнера для применения изменений..." -ForegroundColor Yellow
        docker restart $ContainerName
        
        # Ожидаем указанное количество секунд
        Write-Host "⏱️ Ожидание $WaitSeconds секунд..." -ForegroundColor Yellow
        Start-Sleep -Seconds $WaitSeconds
        
        Write-Host "✓ Контейнер перезапущен" -ForegroundColor Green
    }
    
    Write-Host "✅ Восстановление данных завершено успешно" -ForegroundColor Green
} else {
    Write-Host "⚠️ Ни один файл данных не был восстановлен" -ForegroundColor Yellow
    exit 1
}

exit 0
