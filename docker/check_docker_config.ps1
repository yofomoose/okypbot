# Скрипт проверки Docker конфигурации для okypbot
# Запуск: .\docker\check_docker_config.ps1

Write-Host "🔍 Проверка Docker конфигурации okypbot..." -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Проверяем наличие файлов
Write-Host "`n📁 Проверка наличия файлов:" -ForegroundColor Yellow

$files_to_check = @(
    "docker/Dockerfile",
    "docker/docker-compose.prod.yml",
    "requirements.txt",
    "bot_model/classifier.pkl",
    "bot_model/label_encoder.pkl",
    "bot_model/model_metadata.json"
)

foreach ($file in $files_to_check) {
    if (Test-Path $file) {
        Write-Host "✅ $file - найден" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - отсутствует" -ForegroundColor Red
    }
}

# Проверяем training_examples.pkl (опционально)
if (Test-Path "bot_model/training_examples.pkl") {
    Write-Host "✅ bot_model/training_examples.pkl - найден (данные обучения)" -ForegroundColor Green
} else {
    Write-Host "⚠️  bot_model/training_examples.pkl - отсутствует (опционально)" -ForegroundColor Yellow
}

Write-Host "`n🐳 Проверка Docker:" -ForegroundColor Yellow

# Проверяем Docker
try {
    $dockerVersion = docker --version 2>$null
    Write-Host "✅ Docker установлен: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен или не запущен" -ForegroundColor Red
    exit 1
}

# Проверяем docker-compose
try {
    $composeVersion = docker-compose --version 2>$null
    Write-Host "✅ Docker Compose установлен: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не установлен" -ForegroundColor Red
}

# Проверяем переменные окружения
Write-Host "`n🔧 Проверка переменных окружения:" -ForegroundColor Yellow
Write-Host "Создайте .env файл со следующими переменными:" -ForegroundColor White
Write-Host "  BOT_TOKEN=your_bot_token" -ForegroundColor Gray
Write-Host "  DB_PASSWORD=your_db_password" -ForegroundColor Gray
Write-Host "  OKDESK_API_TOKEN=your_okdesk_token" -ForegroundColor Gray
Write-Host "  OKDESK_BASE_URL=https://your-domain.okdesk.ru" -ForegroundColor Gray
Write-Host "  OKDESK_WEBHOOK_SECRET=your_webhook_secret" -ForegroundColor Gray
Write-Host "  ADMIN_IDS=123456789,987654321" -ForegroundColor Gray

# Проверяем конфигурацию docker-compose
Write-Host "`n📋 Проверка docker-compose конфигурации:" -ForegroundColor Yellow
try {
    docker-compose -f docker/docker-compose.prod.yml config --quiet
    Write-Host "✅ docker-compose.prod.yml - валидная конфигурация" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose.prod.yml - ошибки в конфигурации" -ForegroundColor Red
}

Write-Host "`n🎉 Проверка завершена!" -ForegroundColor Green
Write-Host "`n💡 Для запуска используйте:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker/docker-compose.prod.yml up -d" -ForegroundColor White
Write-Host "`n📊 Для просмотра логов:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker/docker-compose.prod.yml logs -f bot" -ForegroundColor White
