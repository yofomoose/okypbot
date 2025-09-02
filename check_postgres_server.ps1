# PowerShell скрипт для проверки PostgreSQL на сервере

Write-Host "🔍 Проверка подключения к PostgreSQL на сервере" -ForegroundColor Cyan
Write-Host "=============================================="
Write-Host "⏰ Время: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# 1. Проверяем статус Docker контейнеров
Write-Host "🐳 Статус Docker контейнеров:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# 2. Проверяем логи PostgreSQL (последние 20 строк)
Write-Host "📋 Последние логи PostgreSQL:" -ForegroundColor Cyan
docker-compose logs --tail=20 postgres
Write-Host ""

# 3. Проверяем подключение к PostgreSQL изнутри контейнера
Write-Host "🔗 Проверка подключения изнутри контейнера:" -ForegroundColor Cyan
try {
    $result = docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'PostgreSQL работает!' as status, version();" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL доступен изнутри контейнера" -ForegroundColor Green
        Write-Host $result
    } else {
        Write-Host "❌ Ошибка подключения изнутри контейнера" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Ошибка выполнения команды: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. Проверяем таблицы в базе данных
Write-Host "📊 Таблицы в базе данных:" -ForegroundColor Cyan
try {
    $tables = docker exec okypbot_postgres psql -U postgres -d okypbot -c "\dt" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Таблицы получены" -ForegroundColor Green
        Write-Host $tables
    } else {
        Write-Host "⚠️ Таблицы не найдены или ошибка доступа" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Ошибка получения таблиц: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. Проверяем подключение с хоста (если psql установлен)
Write-Host "🌐 Проверка подключения с хоста (порт 5433):" -ForegroundColor Cyan
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlPath) {
    $env:PGPASSWORD = "Cnhjywsq97"
    try {
        $hostResult = psql -h localhost -p 5433 -U postgres -d okypbot -c "SELECT 'Подключение с хоста работает!' as status;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Подключение с хоста работает" -ForegroundColor Green
            Write-Host $hostResult
        } else {
            Write-Host "❌ Ошибка подключения с хоста" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Ошибка подключения с хоста: $($_.Exception.Message)" -ForegroundColor Red
    }
    Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
} else {
    Write-Host "⚠️ psql не установлен на хосте" -ForegroundColor Yellow
}
Write-Host ""

# 6. Проверяем сетевые порты
Write-Host "🔌 Проверка сетевых портов:" -ForegroundColor Cyan
try {
    $ports = netstat -an | Select-String ":543"
    if ($ports) {
        Write-Host "Порты PostgreSQL:"
        $ports | ForEach-Object { Write-Host $_.Line }
    } else {
        Write-Host "⚠️ Порты PostgreSQL не найдены" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка проверки портов: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 7. Проверяем использование ресурсов
Write-Host "📈 Использование ресурсов контейнером PostgreSQL:" -ForegroundColor Cyan
try {
    $stats = docker stats okypbot_postgres --no-stream --format "table {{.Container}}`t{{.CPUPerc}}`t{{.MemUsage}}`t{{.MemPerc}}" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $stats
    } else {
        Write-Host "⚠️ Статистика недоступна" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка получения статистики: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 8. Проверяем переменные окружения
Write-Host "🔧 Переменные окружения PostgreSQL:" -ForegroundColor Cyan
try {
    $envVars = docker exec okypbot_postgres env | Select-String "POSTGRES"
    if ($envVars) {
        $envVars | ForEach-Object { Write-Host $_.Line }
    } else {
        Write-Host "⚠️ Переменные POSTGRES не найдены" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ошибка получения переменных: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 9. Проверяем место на диске
Write-Host "💾 Использование диска:" -ForegroundColor Cyan
try {
    $diskSpace = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, @{Name="PercentFree";Expression={[math]::Round(($_.FreeSpace/$_.Size)*100,2)}}
    $diskSpace | Format-Table -AutoSize
} catch {
    Write-Host "⚠️ Ошибка получения информации о диске: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Итоговый отчет
Write-Host "📊 ИТОГИ ПРОВЕРКИ:" -ForegroundColor Cyan
Write-Host "========================"

# Проверяем, запущен ли контейнер
$containerStatus = docker ps --filter "name=okypbot_postgres" --format "{{.Names}}" 2>$null
if ($containerStatus -match "okypbot_postgres") {
    Write-Host "✅ Контейнер PostgreSQL запущен" -ForegroundColor Green
    
    # Проверяем подключение
    $connectionTest = docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 1;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL доступен и работает" -ForegroundColor Green
        Write-Host "🎉 Все проверки пройдены успешно!" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL запущен, но недоступен" -ForegroundColor Red
        Write-Host "🔧 Рекомендация: Проверьте логи и перезапустите контейнер" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Контейнер PostgreSQL не запущен" -ForegroundColor Red
    Write-Host "🔧 Рекомендация: Запустите контейнеры командой 'docker-compose up -d'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Полезные команды для диагностики:" -ForegroundColor Cyan
Write-Host "docker-compose logs postgres           # Полные логи PostgreSQL" -ForegroundColor Gray
Write-Host "docker exec -it okypbot_postgres bash  # Вход в контейнер" -ForegroundColor Gray
Write-Host "docker-compose restart postgres        # Перезапуск PostgreSQL" -ForegroundColor Gray
Write-Host "docker-compose down; docker-compose up -d  # Полный перезапуск" -ForegroundColor Gray
