# PowerShell скрипт для быстрого исправления nginx upstream проблемы

Write-Host "🔧 Быстрое исправление nginx upstream проблемы" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

# 1. Останавливаем все контейнеры
Write-Host "🛑 Останавливаем контейнеры..." -ForegroundColor Cyan
docker-compose down

# 2. Обновляем nginx конфигурацию
Write-Host "📝 Обновляем nginx конфигурацию..." -ForegroundColor Cyan
$nginxConfig = @"
server {
    listen 80;
    server_name _;

    # Health check
    location /health {
        proxy_pass http://okypbot_app:8001/health;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        access_log off;
    }

    # Webhook endpoint
    location /okdesk-webhook {
        proxy_pass http://okypbot_app:8001/okdesk-webhook;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        client_max_body_size 10M;
    }

    # Root location
    location / {
        proxy_pass http://okypbot_app:8001/;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
    }
}
"@

$nginxConfig | Out-File -FilePath "nginx\default.conf" -Encoding UTF8
Write-Host "✅ nginx конфигурация обновлена" -ForegroundColor Green

# 3. Исправляем docker-compose для правильного порядка запуска
Write-Host "📝 Создаем временный docker-compose с правильными зависимостями..." -ForegroundColor Cyan
$dockerComposeFixed = @"
services:
  postgres:
    image: postgres:15-alpine
    container_name: okypbot_postgres
    environment:
      POSTGRES_DB: okypbot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: `${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C --lc-ctype=C --auth-host=md5"
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backup:/var/lib/postgresql/backup
    ports:
      - "5433:5432"
    restart: unless-stopped
    networks:
      - okypbot-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d okypbot"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  okypbot:
    build: 
      context: .
      dockerfile: docker/Dockerfile
      target: production
    image: okypbot:latest
    container_name: okypbot_app
    environment:
      BOT_TOKEN: `${BOT_TOKEN}
      OKDESK_API_TOKEN: `${OKDESK_API_TOKEN}
      OKDESK_BASE_URL: `${OKDESK_BASE_URL}
      OKDESK_WEBHOOK_SECRET: `${OKDESK_WEBHOOK_SECRET}
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: okypbot
      DB_USER: postgres
      DB_PASSWORD: `${DB_PASSWORD}
      WEBHOOK_ENABLED: 'true'
      WEBHOOK_HOST: 0.0.0.0
      WEBHOOK_PORT: 8001
      ADMIN_IDS: `${ADMIN_IDS}
      PYTHONUNBUFFERED: 1
      PYTHONDONTWRITEBYTECODE: 1
    command: python main.py
    volumes:
      - ./bot_model:/app/bot_model
      - bot_logs:/app/logs
      - bot_data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - okypbot-net
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/health', timeout=5)"]
      interval: 20s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: okypbot_nginx
    ports:
      - "8080:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      okypbot:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - okypbot-net
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  postgres_backup:
  bot_logs:
  bot_data:

networks:
  okypbot-net:
    driver: bridge
"@

$dockerComposeFixed | Out-File -FilePath "docker-compose-fixed.yml" -Encoding UTF8

# 4. Запускаем с исправленной конфигурацией
Write-Host "🚀 Запускаем с исправленной конфигурацией..." -ForegroundColor Cyan
docker-compose -f docker-compose-fixed.yml --env-file .env.production up -d

# 5. Ждем запуска
Write-Host "⏳ Ждем запуска всех сервисов (45 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# 6. Проверяем результат
Write-Host "📊 Проверяем статус контейнеров..." -ForegroundColor Cyan
docker-compose -f docker-compose-fixed.yml ps

Write-Host ""
Write-Host "🔍 Тестируем endpoints..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest "http://localhost:8080/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " ✅ nginx → app health OK" -ForegroundColor Green
} catch {
    Write-Host " ❌ nginx → app health failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Логи nginx..." -ForegroundColor Cyan
docker logs okypbot_nginx | Select-Object -Last 5

Write-Host ""
Write-Host "📋 Логи приложения..." -ForegroundColor Cyan
docker logs okypbot_app | Select-Object -Last 5

Write-Host ""
Write-Host "✅ Исправление завершено!" -ForegroundColor Green
Write-Host "🤖 Попробуйте команду /start в Telegram боте" -ForegroundColor Yellow
Write-Host "🌐 Webhook: http://your-server:8080/okdesk-webhook" -ForegroundColor Yellow
