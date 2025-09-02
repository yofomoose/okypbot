# Скрипт для безопасного обновления бота с сохранением данных регистрации
# Update-BotSafely.ps1

param (
    [string]$ComposeFile = "docker/docker-compose.prod.yml",
    [string]$ContainerName = "okypbot_app",
    [int]$WaitSeconds = 10
)

# Импортируем вспомогательные функции
Import-Module "$PSScriptRoot\PersistenceHelpers.psm1" -Force -ErrorAction SilentlyContinue

# Вывод информации
Write-Host "🔄 Безопасное обновление бота с сохранением данных регистрации..." -ForegroundColor Cyan

# Шаг 1: Создание резервной копии данных регистрации
Write-Host "[1/7] Создание резервной копии данных регистрации..." -ForegroundColor Yellow
& "$PSScriptRoot\Save-RegistrationData.ps1" -ContainerName $ContainerName

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Предупреждение: не удалось создать резервную копию, но продолжаем обновление" -ForegroundColor Yellow
}

# Шаг 2: Обновление кода из Git (если используется)
$isGitRepo = Test-Path ".git"
if ($isGitRepo) {
    Write-Host "[2/7] Получение обновлений из Git..." -ForegroundColor Yellow
    git fetch origin

    # Проверяем, есть ли новые изменения
    $currentCommit = git rev-parse HEAD
    $remoteCommit = git rev-parse '@{u}'
    
    if ($currentCommit -eq $remoteCommit) {
        Write-Host "✓ Бот уже обновлен до последней версии" -ForegroundColor Green
    } else {
        # Получаем изменения
        $pullResult = git pull
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Код успешно обновлен" -ForegroundColor Green
        } else {
            Write-Host "❌ Ошибка при получении обновлений: $pullResult" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "[2/7] Git не используется, пропускаем обновление кода" -ForegroundColor Yellow
}

# Шаг 3: Проверка изменений в requirements.txt
$rebuildNoCache = $false
if ($isGitRepo) {
    Write-Host "[3/7] Проверка изменений в зависимостях..." -ForegroundColor Yellow
    $requirementsChanged = git diff HEAD@{1} --name-only | Select-String -Pattern "requirements.txt"
    
    if ($requirementsChanged) {
        Write-Host "📦 Обнаружены изменения в requirements.txt" -ForegroundColor Yellow
        $rebuildNoCache = $true
    }
} else {
    Write-Host "[3/7] Git не используется, выполним полную пересборку" -ForegroundColor Yellow
    $rebuildNoCache = $true
}

# Шаг 4: Остановка и удаление контейнера
Write-Host "[4/7] Остановка контейнера..." -ForegroundColor Yellow
docker-compose -f $ComposeFile stop bot
docker-compose -f $ComposeFile rm -f bot

# Шаг 5: Пересборка контейнера
Write-Host "[5/7] Пересборка контейнера..." -ForegroundColor Yellow
if ($rebuildNoCache) {
    Write-Host "🔨 Полная пересборка контейнера (--no-cache)" -ForegroundColor Yellow
    docker-compose -f $ComposeFile build --no-cache bot
} else {
    Write-Host "🔨 Быстрая пересборка контейнера" -ForegroundColor Yellow
    docker-compose -f $ComposeFile build bot
}

# Шаг 6: Запуск контейнера
Write-Host "[6/7] Запуск контейнера..." -ForegroundColor Yellow
docker-compose -f $ComposeFile up -d bot

# Ожидание полной инициализации контейнера
Write-Host "⏱️ Ожидание $WaitSeconds секунд для инициализации контейнера..." -ForegroundColor Yellow
Start-Sleep -Seconds $WaitSeconds

# Шаг 7: Восстановление данных регистрации
Write-Host "[7/7] Восстановление данных регистрации..." -ForegroundColor Yellow
& "$PSScriptRoot\Restore-RegistrationData.ps1" -ContainerName $ContainerName -WaitSeconds 5

# Проверяем статус контейнера
Write-Host "📊 Проверка статуса контейнера:" -ForegroundColor Yellow
docker ps --filter "name=$ContainerName"

# Проверяем логи
Write-Host "📜 Последние записи в логе:" -ForegroundColor Yellow
docker logs --tail 20 $ContainerName

Write-Host "✅ Бот успешно обновлен с сохранением данных регистрации!" -ForegroundColor Green
Write-Host "💡 Для просмотра полных логов выполните: docker logs $ContainerName" -ForegroundColor Blue
