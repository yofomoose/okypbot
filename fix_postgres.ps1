# PowerShell скрипт для исправления проблем с PostgreSQL в Docker

Write-Host "🔧 Исправление проблем с PostgreSQL" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Yellow

# 1. Останавливаем все контейнеры
Write-Host "🛑 Останавливаем контейнеры..." -ForegroundColor Cyan
docker-compose down

# 2. Проверяем и создаем правильный .env файл
Write-Host "📝 Проверяем конфигурацию..." -ForegroundColor Cyan

$envContent = @"
# Okdesk CRM Telegram Bot - Production Configuration

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

# Создаем .env файл для Docker
$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Создан .env файл для Docker" -ForegroundColor Green

# 3. Запускаем только PostgreSQL
Write-Host "🐘 Запускаем PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d postgres

# Ждем запуска
Write-Host "⏳ Ждем запуска PostgreSQL (30 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 4. Настраиваем базу данных
Write-Host "📋 Настраиваем базу данных..." -ForegroundColor Cyan

# Создаем базу данных
docker exec okypbot_postgres psql -U postgres -c "CREATE DATABASE okypbot;" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ℹ️ База данных уже существует" -ForegroundColor Yellow
}

# Устанавливаем пароль
docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Пароль PostgreSQL установлен" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка установки пароля" -ForegroundColor Red
}

# 5. Проверяем подключение
Write-Host "🔍 Проверяем подключение..." -ForegroundColor Cyan
$connectionTest = docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT version();" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL настроен правильно!" -ForegroundColor Green
    
    # 6. Пересобираем и запускаем приложение
    Write-Host "🔨 Пересобираем приложение..." -ForegroundColor Cyan
    docker-compose build --no-cache okypbot
    
    Write-Host "🚀 Запускаем основное приложение..." -ForegroundColor Cyan
    docker-compose up -d
    
    Start-Sleep -Seconds 10
    
    Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "🎉 Настройка завершена!" -ForegroundColor Green
    Write-Host "📝 Логи можно посмотреть командой: docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "🌐 Webhook доступен на: http://localhost:8001/okdesk-webhook" -ForegroundColor Yellow
    
} else {
    Write-Host "❌ Ошибка настройки PostgreSQL" -ForegroundColor Red
    Write-Host "📋 Логи PostgreSQL:" -ForegroundColor Yellow
    docker-compose logs postgres
}

Write-Host ""
Write-Host "🔧 Дополнительные команды для отладки:" -ForegroundColor Cyan
Write-Host "docker-compose logs postgres    # Логи PostgreSQL" -ForegroundColor Gray
Write-Host "docker-compose logs okypbot     # Логи приложения" -ForegroundColor Gray
Write-Host "docker exec -it okypbot_postgres psql -U postgres -d okypbot  # Подключение к БД" -ForegroundColor Gray
