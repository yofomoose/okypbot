# Скрипт для исправления проблемы сохранения данных
# Fix-DataPersistence.ps1

param (
    [string]$ComposeFile = "docker/docker-compose.prod.yml",
    [string]$ContainerName = "okypbot_app"
)

# Импортируем вспомогательные функции
Import-Module "$PSScriptRoot\PersistenceHelpers.psm1" -Force -ErrorAction SilentlyContinue

# Вывод информации
Write-Host "🔧 Исправление проблемы сохранения данных при пересборке контейнера..." -ForegroundColor Cyan

# Шаг 1: Проверка структуры данных в проекте
Write-Host "[1/4] Проверка структуры данных..." -ForegroundColor Yellow
python -m scripts.fix_data_persistence
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при выполнении скрипта fix_data_persistence.py" -ForegroundColor Red
    exit 1
}

# Шаг 2: Безопасная пересборка контейнера с сохранением данных
Write-Host "[2/4] Безопасная пересборка контейнера..." -ForegroundColor Yellow
& "$PSScriptRoot\Rebuild-BotSafely.ps1" -ComposeFile $ComposeFile -ContainerName $ContainerName
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при безопасной пересборке контейнера" -ForegroundColor Red
    exit 1
}

# Шаг 3: Создание директории для резервных копий в контейнере
Write-Host "[3/4] Настройка директории для данных в контейнере..." -ForegroundColor Yellow
docker exec -i $ContainerName mkdir -p /app/database
docker exec -i $ContainerName chmod 777 /app/database
Write-Host "✓ Директория для данных настроена" -ForegroundColor Green

# Шаг 4: Проверка результата
Write-Host "[4/4] Проверка результата..." -ForegroundColor Yellow

# Проверяем, что директория существует
$dirExists = docker exec -i $ContainerName ls -la /app/database
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Директория /app/database существует в контейнере" -ForegroundColor Green
} else {
    Write-Host "❌ Директория /app/database не создана в контейнере" -ForegroundColor Red
}

# Создаем тестовый файл в директории
Write-Host "📝 Создание тестового файла в директории..." -ForegroundColor Yellow
docker exec -i $ContainerName bash -c "echo 'Test data' > /app/database/test_persistence.txt"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Тестовый файл успешно создан" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка при создании тестового файла" -ForegroundColor Red
}

Write-Host "✅ Проблема сохранения данных успешно исправлена" -ForegroundColor Green
Write-Host "💡 Теперь при обновлении используйте:" -ForegroundColor Blue
Write-Host "   .\scripts\Update-BotSafely.ps1" -ForegroundColor Blue
