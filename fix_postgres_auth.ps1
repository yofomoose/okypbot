# PowerShell скрипт для исправления аутентификации PostgreSQL

Write-Host "🔧 Исправление аутентификации PostgreSQL" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# Устанавливаем пароль для пользователя postgres
Write-Host "🔑 Устанавливаем пароль для пользователя postgres..." -ForegroundColor Cyan
$passwordResult = docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Пароль успешно установлен" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка установки пароля" -ForegroundColor Red
    exit 1
}

# Проверяем подключение с паролем
Write-Host ""
Write-Host "🔍 Проверяем подключение с паролем..." -ForegroundColor Cyan
$env:PGPASSWORD = "Cnhjywsq97"
$connectionResult = docker exec okypbot_postgres psql -U postgres -d okypbot -h localhost -c "SELECT 'Подключение с паролем работает!' as status;"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Подключение с паролем работает!" -ForegroundColor Green
} else {
    Write-Host "❌ Подключение с паролем не работает" -ForegroundColor Red
    
    # Пытаемся обновить pg_hba.conf для использования md5 вместо scram-sha-256
    Write-Host "🔧 Обновляем настройки аутентификации..." -ForegroundColor Cyan
    docker exec okypbot_postgres sed -i 's/scram-sha-256/md5/g' /var/lib/postgresql/data/pgdata/pg_hba.conf
    
    # Перезагружаем конфигурацию
    docker exec okypbot_postgres psql -U postgres -c "SELECT pg_reload_conf();"
    
    Write-Host "⏳ Ждем применения настроек..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Проверяем снова
    $env:PGPASSWORD = "Cnhjywsq97"
    docker exec okypbot_postgres psql -U postgres -d okypbot -h localhost -c "SELECT 'Подключение после настройки работает!' as status;"
}

Write-Host ""
Write-Host "📊 Проверяем логи приложения..." -ForegroundColor Cyan
docker logs okypbot_app | Select-Object -Last 10

Write-Host ""
Write-Host "✅ Исправление завершено!" -ForegroundColor Green

# Очищаем переменную пароля
Remove-Item Env:PGPASSWORD
