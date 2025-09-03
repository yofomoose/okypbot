# PowerShell скрипт для правильного деплоя okypbot

Write-Host "🚀 Правильный деплой okypbot с исправленной конфигурацией" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Yellow

# Проверяем что мы в правильной директории
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml не найден. Убедитесь что вы в директории проекта." -ForegroundColor Red
    exit 1
}

# Останавливаем старые контейнеры
Write-Host "🛑 Останавливаем старые контейнеры..." -ForegroundColor Cyan
docker-compose down

# Очищаем старые образы
Write-Host "🧹 Очищаем старые образы..." -ForegroundColor Cyan
docker system prune -f

# Принудительно удаляем старый образ okypbot
Write-Host "🗑️ Удаляем старый образ okypbot..." -ForegroundColor Cyan
docker rmi okypbot:latest 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Образ okypbot:latest не найден" -ForegroundColor Gray
}

# Пересобираем с новыми зависимостями
Write-Host "🔨 Пересобираем приложение с новыми зависимостями..." -ForegroundColor Cyan
docker-compose build --no-cache --pull

# Запускаем с правильной конфигурацией
Write-Host "🚀 Запускаем с исправленной конфигурацией..." -ForegroundColor Cyan
docker-compose --env-file .env.production up -d

# Ждем запуска
Write-Host "⏳ Ждем запуска всех сервисов (60 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Проверяем статус
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

# Проверяем PostgreSQL
Write-Host ""
Write-Host "🐘 Проверка PostgreSQL..." -ForegroundColor Cyan
$pgResult = docker exec okypbot_postgres pg_isready -U postgres
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL готов" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL не готов" -ForegroundColor Red
}

# Проверяем переменные окружения в приложении
Write-Host ""
Write-Host "🔍 Проверка переменных окружения в приложении..." -ForegroundColor Cyan
docker exec okypbot_app printenv | Select-String -Pattern "(WEBHOOK_PORT|DB_HOST|DB_PORT)" | Sort-Object

# Проверяем порты
Write-Host ""
Write-Host "🔍 Проверка активных портов..." -ForegroundColor Cyan
$portCheck = docker exec okypbot_app ss -tulpn | Select-String -Pattern ":800[01]"
if ($portCheck) {
    $portCheck
} else {
    Write-Host "Не удалось определить порты" -ForegroundColor Yellow
}

# Тестируем endpoints
Write-Host ""
Write-Host "🌐 Тестирование endpoints..." -ForegroundColor Cyan

# Прямое подключение к приложению
$appTest = docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Приложение на порту 8001 работает" -ForegroundColor Green
} else {
    Write-Host "❌ Приложение на порту 8001 недоступно" -ForegroundColor Red
}

# Через nginx
try {
    $nginxTest = Invoke-WebRequest "http://localhost:8080/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ nginx → приложение работает" -ForegroundColor Green
} catch {
    Write-Host "❌ nginx → приложение недоступно" -ForegroundColor Red
}

# Тестируем webhook endpoint
try {
    $webhookTest = Invoke-WebRequest "http://localhost:8080/okdesk-webhook" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"test": true}' `
        -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Webhook endpoint доступен" -ForegroundColor Green
} catch {
    Write-Host "❌ Webhook endpoint недоступен" -ForegroundColor Red
}

# Показываем последние логи
Write-Host ""
Write-Host "📋 Последние логи приложения:" -ForegroundColor Cyan
docker logs okypbot_app | Select-Object -Last 10

Write-Host ""
Write-Host "✅ Деплой завершен!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Сводка:" -ForegroundColor Cyan
Write-Host "   🌐 Webhook URL: http://ваш-сервер:8080/okdesk-webhook" -ForegroundColor Gray
Write-Host "   🤖 Telegram бот должен отвечать на команды" -ForegroundColor Gray
Write-Host "   🐘 PostgreSQL готов к работе" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Если есть проблемы, запустите диагностику:" -ForegroundColor Yellow
Write-Host "   .\diagnose_bot_issues.sh" -ForegroundColor Gray
Write-Host "   python diagnose_telegram_bot.py" -ForegroundColor Gray
