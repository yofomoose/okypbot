# Скрипт для пересборки бота с сохранением данных регистрации
# Rebuild-BotSafely.ps1

param (
    [string]$ComposeFile = "docker/docker-compose.prod.yml",
    [string]$ContainerName = "okypbot_app",
    [int]$WaitSeconds = 10,
    [switch]$NoCache = $true
)

# Импортируем вспомогательные функции
Import-Module "$PSScriptRoot\PersistenceHelpers.psm1" -Force -ErrorAction SilentlyContinue

# Вывод информации
Write-Host "🏗️ Безопасная пересборка бота с сохранением данных регистрации..." -ForegroundColor Cyan

# Шаг 1: Создание резервной копии данных регистрации
Write-Host "[1/5] Создание резервной копии данных регистрации..." -ForegroundColor Yellow
& "$PSScriptRoot\Save-RegistrationData.ps1" -ContainerName $ContainerName

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Предупреждение: не удалось создать резервную копию, но продолжаем пересборку" -ForegroundColor Yellow
}

# Шаг 2: Остановка и удаление контейнера
Write-Host "[2/5] Остановка контейнера..." -ForegroundColor Yellow
docker-compose -f $ComposeFile stop bot
docker-compose -f $ComposeFile rm -f bot

# Шаг 3: Пересборка контейнера
Write-Host "[3/5] Пересборка контейнера..." -ForegroundColor Yellow
if ($NoCache) {
    Write-Host "🔨 Полная пересборка контейнера (--no-cache)" -ForegroundColor Yellow
    docker-compose -f $ComposeFile build --no-cache bot
} else {
    Write-Host "🔨 Быстрая пересборка контейнера" -ForegroundColor Yellow
    docker-compose -f $ComposeFile build bot
}

# Шаг 4: Запуск контейнера
Write-Host "[4/5] Запуск контейнера..." -ForegroundColor Yellow
docker-compose -f $ComposeFile up -d bot

# Ожидание полной инициализации контейнера
Write-Host "⏱️ Ожидание $WaitSeconds секунд для инициализации контейнера..." -ForegroundColor Yellow
Start-Sleep -Seconds $WaitSeconds

# Шаг 5: Восстановление данных регистрации
Write-Host "[5/5] Восстановление данных регистрации..." -ForegroundColor Yellow
& "$PSScriptRoot\Restore-RegistrationData.ps1" -ContainerName $ContainerName -WaitSeconds 5

# Проверяем статус контейнера
Write-Host "📊 Проверка статуса контейнера:" -ForegroundColor Yellow
docker ps --filter "name=$ContainerName"

Write-Host "✅ Бот успешно пересобран с сохранением данных регистрации!" -ForegroundColor Green
Write-Host "💡 Для просмотра логов выполните: docker logs $ContainerName" -ForegroundColor Blue
