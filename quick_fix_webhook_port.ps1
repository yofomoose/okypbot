# PowerShell скрипт для быстрого исправления порта webhook

Write-Host "⚡ Быстрое исправление порта webhook и обновление" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow

# Останавливаем текущие контейнеры
Write-Host "🛑 Останавливаем контейнеры..." -ForegroundColor Cyan
docker-compose down

# Проверяем переменные окружения
Write-Host "🔍 Проверяем текущие переменные окружения..." -ForegroundColor Cyan
Write-Host "В .env.production:" -ForegroundColor Gray
Get-Content .env.production | Select-String "WEBHOOK_PORT"

Write-Host ""
Write-Host "В docker-compose.yml:" -ForegroundColor Gray
Get-Content docker-compose.yml | Select-String "WEBHOOK_PORT"

# Принудительно устанавливаем переменную окружения
Write-Host ""
Write-Host "🔧 Устанавливаем переменную окружения..." -ForegroundColor Cyan
$env:WEBHOOK_PORT = "8001"

# Запускаем с форсированными переменными окружения
Write-Host "🚀 Перезапускаем с правильными настройками..." -ForegroundColor Cyan
docker-compose --env-file .env.production up -d --force-recreate

Write-Host "⏳ Ждем запуска (30 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Проверяем переменные окружения в контейнере
Write-Host "🔍 Проверяем переменные в запущенном контейнере..." -ForegroundColor Cyan
docker exec okypbot_app printenv | Select-String "WEBHOOK"

# Проверяем на каком порту слушает приложение
Write-Host ""
Write-Host "🔍 Проверяем активные порты в контейнере..." -ForegroundColor Cyan
$netstatResult = docker exec okypbot_app netstat -tulpn 2>$null | Select-String ":800"
if (-not $netstatResult) {
    docker exec okypbot_app ss -tulpn | Select-String ":800"
}

# Тестируем оба порта
Write-Host ""
Write-Host "🔍 Тестируем доступность портов..." -ForegroundColor Cyan
$port8000 = docker exec okypbot_app curl -s "http://localhost:8000/health" -m 5 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Порт 8000 работает" -ForegroundColor Green
} else {
    Write-Host "❌ Порт 8000 недоступен" -ForegroundColor Red
}

$port8001 = docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Порт 8001 работает" -ForegroundColor Green
} else {
    Write-Host "❌ Порт 8001 недоступен" -ForegroundColor Red
}

# Проверяем через nginx
Write-Host ""
Write-Host "🌐 Тестируем через nginx..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest "http://localhost:8080/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ nginx → приложение работает" -ForegroundColor Green
} catch {
    Write-Host "❌ nginx → приложение недоступно" -ForegroundColor Red
}

# Показываем логи для диагностики
Write-Host ""
Write-Host "📋 Последние логи приложения..." -ForegroundColor Cyan
docker logs okypbot_app | Select-Object -Last 10

Write-Host ""
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "✅ Исправление завершено!" -ForegroundColor Green
Write-Host "🤖 Попробуйте команду /start в Telegram боте" -ForegroundColor Yellow
Write-Host "🌐 Webhook должен быть доступен на: http://your-server:8080/okdesk-webhook" -ForegroundColor Yellow

# Очищаем переменную окружения
Remove-Item Env:WEBHOOK_PORT -ErrorAction SilentlyContinue
