# PowerShell версия проверки PostgreSQL в Docker

Write-Host "🔍 Проверка подключения к PostgreSQL в Docker" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow

# Проверяем статус контейнеров
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🐘 Проверка PostgreSQL:" -ForegroundColor Cyan

# Простая проверка подключения
Write-Host "1. Проверка версии PostgreSQL:" -ForegroundColor Green
docker exec okypbot_postgres psql -U postgres -c "SELECT version();"

Write-Host ""
Write-Host "2. Список баз данных:" -ForegroundColor Green
docker exec okypbot_postgres psql -U postgres -c "\l"

Write-Host ""
Write-Host "3. Проверка подключения к базе okypbot:" -ForegroundColor Green
docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"

Write-Host ""
Write-Host "4. Проверка таблиц в базе okypbot:" -ForegroundColor Green
docker exec okypbot_postgres psql -U postgres -d okypbot -c "\dt"

Write-Host ""
Write-Host "5. Тест простого запроса:" -ForegroundColor Green
docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'PostgreSQL работает!' as status;"

Write-Host ""
Write-Host "✅ Проверка завершена!" -ForegroundColor Green
