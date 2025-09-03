#!/usr/bin/env pwsh
# Скрипт для перезапуска бота с исправлениями numpy и прав доступа

Write-Host "🔄 Перезапуск бота с исправлениями..." -ForegroundColor Yellow

# Останавливаем контейнеры
Write-Host "⏹️ Остановка контейнеров..." -ForegroundColor Blue
docker compose down

# Очищаем старые образы для принудительной пересборки
Write-Host "🧹 Очистка старых образов..." -ForegroundColor Blue
docker image prune -f
docker compose build --no-cache bot

# Запускаем сервисы
Write-Host "🚀 Запуск обновленных сервисов..." -ForegroundColor Green
docker compose up -d

# Ждем запуска
Start-Sleep -Seconds 10

# Проверяем логи
Write-Host "📋 Проверка логов..." -ForegroundColor Cyan
docker compose logs --tail=50 bot

Write-Host "✅ Перезапуск завершен!" -ForegroundColor Green
Write-Host "🔍 Для просмотра логов используйте: docker compose logs -f bot" -ForegroundColor Yellow
