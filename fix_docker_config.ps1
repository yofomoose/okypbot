# PowerShell скрипт для исправления конфигурации Docker и перезапуска

Write-Host "🔧 Исправление конфигурации Docker и перезапуск" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Yellow

# Останавливаем контейнеры
Write-Host "🛑 Останавливаем контейнеры..." -ForegroundColor Cyan
docker-compose down

# Очищаем старые образы
Write-Host "🧹 Очищаем старые образы..." -ForegroundColor Cyan
docker system prune -f

# Пересобираем с новой конфигурацией  
Write-Host "🔨 Пересобираем приложение..." -ForegroundColor Cyan
docker-compose build --no-cache

# Запускаем заново
Write-Host "🚀 Запускаем с исправленной конфигурацией..." -ForegroundColor Cyan
docker-compose --env-file .env.production up -d

# Ждем запуска
Write-Host "⏳ Ждем запуска контейнеров..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Проверяем статус
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "📋 Логи PostgreSQL:" -ForegroundColor Cyan
docker-compose logs postgres | Select-Object -Last 10

Write-Host ""
Write-Host "📋 Логи приложения:" -ForegroundColor Cyan  
docker-compose logs okypbot | Select-Object -Last 10

Write-Host ""
Write-Host "🔍 Проверка подключения к PostgreSQL..." -ForegroundColor Cyan
docker exec okypbot_postgres pg_isready -U postgres

Write-Host ""
Write-Host "✅ Перезапуск завершен!" -ForegroundColor Green
Write-Host "🌐 Webhook доступен на: http://localhost:8080/okdesk-webhook" -ForegroundColor Yellow
