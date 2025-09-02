# PowerShell скрипт для исправления проблем с паролем PostgreSQL

Write-Host "🔧 Исправление проблем с паролем PostgreSQL" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Yellow

# 1. Останавливаем приложение, но оставляем PostgreSQL
Write-Host "🛑 Останавливаем приложение..." -ForegroundColor Cyan
docker stop okypbot_app 2>$null

# 2. Исправляем пароль PostgreSQL
Write-Host "🔑 Исправляем пароль PostgreSQL..." -ForegroundColor Cyan
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Пароль обновлен" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка обновления пароля" -ForegroundColor Red
}

# 3. Перезагружаем конфигурацию PostgreSQL
Write-Host "🔄 Перезагружаем конфигурацию PostgreSQL..." -ForegroundColor Cyan
docker exec okypbot_postgres psql -U postgres -c "SELECT pg_reload_conf();"

# 4. Тестируем подключение с паролем
Write-Host "🧪 Тестируем подключение с паролем..." -ForegroundColor Cyan
$env:PGPASSWORD = 'Cnhjywsq97'
$testResult = docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'Подключение с паролем работает!' as test;" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Подключение с паролем работает" -ForegroundColor Green
} else {
    Write-Host "❌ Подключение с паролем не работает" -ForegroundColor Red
}

# 5. Создаем правильный .env файл
Write-Host "📝 Создаем правильный .env файл..." -ForegroundColor Cyan

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

# Webhook настройки
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001

# Администраторы
ADMIN_IDS=413129274,398258337

# Debug
DEBUG=false
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ .env файл создан" -ForegroundColor Green

# 6. Пересобираем и запускаем приложение
Write-Host "🔨 Пересобираем приложение..." -ForegroundColor Cyan
docker-compose build --no-cache okypbot

Write-Host "🚀 Запускаем приложение..." -ForegroundColor Cyan
docker-compose up -d okypbot

# 7. Ждем запуска и проверяем логи
Write-Host "⏳ Ждем запуска (10 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "📋 Проверяем логи приложения:" -ForegroundColor Cyan
docker logs okypbot_app --tail 20

Write-Host ""
Write-Host "📋 Последние логи PostgreSQL:" -ForegroundColor Cyan
docker logs okypbot_postgres --tail 10

Write-Host ""
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🎯 Результат:" -ForegroundColor Cyan
$appLogs = docker logs okypbot_app 2>&1
if ($appLogs -match "password authentication failed") {
    Write-Host "❌ Все еще есть проблемы с паролем" -ForegroundColor Red
    Write-Host "💡 Попробуйте полный перезапуск PostgreSQL:" -ForegroundColor Yellow
    Write-Host "   docker-compose down" -ForegroundColor Gray
    Write-Host "   docker volume rm okypbot_postgres_data" -ForegroundColor Gray
    Write-Host "   docker-compose up -d" -ForegroundColor Gray
} else {
    Write-Host "✅ Проблемы с паролем устранены!" -ForegroundColor Green
}
