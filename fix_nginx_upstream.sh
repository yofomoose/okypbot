#!/bin/bash

echo "🔧 Быстрое исправление nginx upstream проблемы"
echo "============================================"

# 1. Останавливаем все контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose down

# 2. Обновляем nginx конфигурацию
echo "📝 Обновляем nginx конфигурацию..."
cat > nginx/default.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # Health check
    location /health {
        proxy_pass http://okypbot_app:8001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        access_log off;
    }

    # Webhook endpoint
    location /okdesk-webhook {
        proxy_pass http://okypbot_app:8001/okdesk-webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        client_max_body_size 10M;
    }

    # Root location
    location / {
        proxy_pass http://okypbot_app:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

echo "✅ nginx конфигурация обновлена"

# 3. Исправляем docker-compose для правильного порядка запуска
echo "📝 Создаем временный docker-compose с правильными зависимостями..."
cat > docker-compose-fixed.yml << 'EOF'
services:
  postgres:
    image: postgres:15-alpine
    container_name: okypbot_postgres
    environment:
      POSTGRES_DB: okypbot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
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
      BOT_TOKEN: ${BOT_TOKEN}
      OKDESK_API_TOKEN: ${OKDESK_API_TOKEN}
      OKDESK_BASE_URL: ${OKDESK_BASE_URL}
      OKDESK_WEBHOOK_SECRET: ${OKDESK_WEBHOOK_SECRET}
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: okypbot
      DB_USER: postgres
      DB_PASSWORD: ${DB_PASSWORD}
      WEBHOOK_ENABLED: 'true'
      WEBHOOK_HOST: 0.0.0.0
      WEBHOOK_PORT: 8001
      ADMIN_IDS: ${ADMIN_IDS}
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
EOF

# 4. Запускаем с исправленной конфигурацией
echo "🚀 Запускаем с исправленной конфигурацией..."
docker-compose -f docker-compose-fixed.yml --env-file .env.production up -d

# 5. Ждем запуска
echo "⏳ Ждем запуска всех сервисов (45 секунд)..."
sleep 45

# 6. Проверяем результат
echo "📊 Проверяем статус контейнеров..."
docker-compose -f docker-compose-fixed.yml ps

echo ""
echo "🔍 Тестируем endpoints..."
curl -s "http://localhost:8080/health" && echo " ✅ nginx → app health OK" || echo " ❌ nginx → app health failed"

echo ""
echo "📋 Логи nginx..."
docker logs okypbot_nginx | tail -5

echo ""
echo "📋 Логи приложения..."
docker logs okypbot_app | tail -5

echo ""
echo "✅ Исправление завершено!"
echo "🤖 Попробуйте команду /start в Telegram боте"
echo "🌐 Webhook: http://your-server:8080/okdesk-webhook"
EOF
