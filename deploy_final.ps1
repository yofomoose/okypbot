# PowerShell скрипт для финального деплоя с исправлением всех проблем

Write-Host "🚀 Финальный деплой с исправлением всех проблем" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Yellow

# 1. Останавливаем все контейнеры
Write-Host "🛑 Останавливаем все контейнеры..." -ForegroundColor Cyan
docker-compose down
docker stop $(docker ps -aq) 2>$null
docker system prune -f

# 2. Удаляем проблемные volumes если есть
Write-Host "🧹 Очищаем проблемные volumes..." -ForegroundColor Cyan
docker volume prune -f

# 3. Принудительно устанавливаем переменные окружения
Write-Host "📝 Устанавливаем переменные окружения..." -ForegroundColor Cyan
$env:WEBHOOK_PORT = "8001"
$env:WEBHOOK_HOST = "0.0.0.0"
$env:WEBHOOK_ENABLED = "true"

# 4. Создаем правильный .env файл для Docker
Write-Host "📋 Создаем правильный .env файл..." -ForegroundColor Cyan
$envContent = @"
# Telegram Bot Token
BOT_TOKEN=8461903171:AAFKNyFL5LcqFIHSaGePJZ-vCCNQU3kRIqA

# Okdesk API Token
OKDESK_API_TOKEN=4cf96e5bb33f06481e4aff5ff0a2aa740ce8490a

# Базовый URL вашего аккаунта Okdesk
OKDESK_BASE_URL=https://yapomogu55.okdesk.ru

# ID автора для комментариев
OKDESK_AUTHOR_ID=1

# PostgreSQL Configuration для Docker
DB_HOST=postgres
DB_PORT=5432
DB_NAME=okypbot
DB_USER=postgres
DB_PASSWORD=Cnhjywsq97

# Webhook настройки - ФИКСИРОВАННО
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001

# Администраторы
ADMIN_IDS=413129274,398258337

# Debug
DEBUG=false
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8

# 5. Пересобираем образ без кэша
Write-Host "🔨 Пересобираем образ..." -ForegroundColor Cyan
docker-compose build --no-cache --pull

# 6. Запускаем с принудительными переменными
Write-Host "🚀 Запускаем с правильными настройками..." -ForegroundColor Cyan
$env:WEBHOOK_PORT = "8001"
$env:WEBHOOK_HOST = "0.0.0.0" 
$env:WEBHOOK_ENABLED = "true"
docker-compose up -d --force-recreate

# 7. Ждем полного запуска
Write-Host "⏳ Ждем полного запуска (45 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# 8. Проверяем результат
Write-Host "📊 Проверяем статус..." -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🔍 Проверяем переменные в контейнере..." -ForegroundColor Cyan
docker exec okypbot_app printenv | Select-String -Pattern "WEBHOOK|BOT_TOKEN" | Select-Object -First 5

Write-Host ""
Write-Host "🔍 Проверяем порты..." -ForegroundColor Cyan
$portInfo = docker exec okypbot_app ss -tulpn 2>$null | Select-String ":800"
if ($portInfo) {
    $portInfo
} else {
    Write-Host "Не удалось получить информацию о портах" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🌐 Тестируем endpoints..." -ForegroundColor Cyan

# Тест напрямую к приложению
$appTest = docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Приложение на 8001 работает" -ForegroundColor Green
} else {
    Write-Host "❌ Приложение на 8001 недоступно" -ForegroundColor Red
}

# Тест через nginx
try {
    $response = Invoke-WebRequest "http://localhost:8080/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ nginx → приложение работает" -ForegroundColor Green
} catch {
    Write-Host "❌ nginx → приложение недоступно" -ForegroundColor Red
}

# Тест webhook endpoint
try {
    $response = Invoke-WebRequest "http://localhost:8080/okdesk-webhook" -Method POST -ContentType "application/json" -Body '{"test": true}' -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ webhook endpoint работает" -ForegroundColor Green
} catch {
    Write-Host "❌ webhook endpoint недоступен" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Последние логи приложения..." -ForegroundColor Cyan
docker logs okypbot_app | Select-Object -Last 10

Write-Host ""
Write-Host "✅ Деплой завершен!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Проверьте что бот отвечает на команду /start в Telegram" -ForegroundColor Gray
Write-Host "2. Настройте webhook в Okdesk на URL: http://your-server:8080/okdesk-webhook" -ForegroundColor Gray
Write-Host "3. Протестируйте создание заявки в боте" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Если проблемы остались:" -ForegroundColor Yellow
Write-Host "   docker logs okypbot_app" -ForegroundColor Gray
Write-Host "   docker exec -it okypbot_app bash" -ForegroundColor Gray

# Очищаем переменные окружения
Remove-Item Env:WEBHOOK_PORT -ErrorAction SilentlyContinue
Remove-Item Env:WEBHOOK_HOST -ErrorAction SilentlyContinue  
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
