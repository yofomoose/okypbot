#!/bin/bash
# Скрипт для исправления проблем с nginx и доступом к директориям

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Сброс цвета

echo -e "${BLUE}=== Скрипт исправления проблем с nginx и доступом к директориям ===${NC}"

# Проверяем, существуют ли контейнеры
if ! docker ps -a | grep -q okypbot_app; then
    echo -e "${RED}❌ Контейнер okypbot_app не найден!${NC}"
    exit 1
fi

if ! docker ps -a | grep -q okypbot_nginx; then
    echo -e "${RED}❌ Контейнер okypbot_nginx не найден!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Контейнеры найдены${NC}"

# 1. Исправляем проблему с разрешениями в директории bot_model
echo -e "${YELLOW}Исправление прав доступа в директории bot_model...${NC}"
docker exec -it okypbot_app bash -c "chmod -R 777 /app/bot_model || true"

# 2. Исправляем проблему с nginx конфигурацией

# Проверяем содержимое текущей конфигурации
echo -e "${YELLOW}Проверка текущей конфигурации nginx...${NC}"
NGINX_CONFIG=$(docker exec -it okypbot_nginx cat /etc/nginx/conf.d/default.conf)

# Проверяем, содержит ли конфигурация правильные настройки
if echo "$NGINX_CONFIG" | grep -q "proxy_pass http://bot:8000/okdesk-webhook"; then
    echo -e "${GREEN}✅ Конфигурация nginx содержит правильное проксирование для /okdesk-webhook${NC}"
else
    echo -e "${RED}❌ Конфигурация nginx неправильная!${NC}"
    
    echo -e "${YELLOW}Создание новой конфигурации nginx...${NC}"
    
    # Создаем временный Dockerfile для nginx
    echo -e "${YELLOW}Создание временного Dockerfile для nginx...${NC}"
    cat > nginx/Dockerfile.tmp << EOF
FROM nginx:alpine
COPY default.conf /etc/nginx/conf.d/default.conf
EOF

    # Убеждаемся, что файл default.conf существует
    if [ ! -f "nginx/default.conf" ] || [ ! -f "nginx/default.conf.new" ]; then
        echo -e "${RED}❌ Не найден файл конфигурации nginx!${NC}"
        exit 1
    fi
    
    # Копируем новую конфигурацию
    cp nginx/default.conf.new nginx/default.conf
    
    # Создаем новый образ
    echo -e "${YELLOW}Сборка нового образа nginx...${NC}"
    docker build -t okypbot-nginx:latest -f nginx/Dockerfile.tmp nginx/
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Ошибка сборки образа nginx!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Образ nginx успешно собран${NC}"
    
    # Останавливаем и удаляем текущий контейнер nginx
    echo -e "${YELLOW}Остановка и удаление текущего контейнера nginx...${NC}"
    docker stop okypbot_nginx
    docker rm okypbot_nginx
    
    # Запускаем новый контейнер с новым образом
    echo -e "${YELLOW}Запуск нового контейнера nginx с правильной конфигурацией...${NC}"
    docker run -d \
        --name okypbot_nginx \
        --network okypbot-net \
        -p 8080:80 \
        --restart unless-stopped \
        okypbot-nginx:latest
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Ошибка запуска контейнера nginx!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Новый контейнер nginx успешно запущен${NC}"
fi

# 3. Проверяем установку зависимостей FastAPI и uvicorn
echo -e "${YELLOW}Проверка установки FastAPI и uvicorn...${NC}"
FASTAPI_INSTALLED=$(docker exec -it okypbot_app pip list | grep -i fastapi || echo "not installed")
UVICORN_INSTALLED=$(docker exec -it okypbot_app pip list | grep -i uvicorn || echo "not installed")

if [[ "$FASTAPI_INSTALLED" == *"not installed"* ]]; then
    echo -e "${RED}❌ FastAPI не установлен!${NC}"
    echo -e "${YELLOW}Установка FastAPI...${NC}"
    docker exec -it okypbot_app pip install fastapi==0.100.1
else
    echo -e "${GREEN}✅ FastAPI установлен: $FASTAPI_INSTALLED${NC}"
fi

if [[ "$UVICORN_INSTALLED" == *"not installed"* ]]; then
    echo -e "${RED}❌ uvicorn не установлен!${NC}"
    echo -e "${YELLOW}Установка uvicorn...${NC}"
    docker exec -it okypbot_app pip install "uvicorn[standard]==0.23.2"
else
    echo -e "${GREEN}✅ uvicorn установлен: $UVICORN_INSTALLED${NC}"
fi

# 4. Перезапускаем контейнер с ботом
echo -e "${YELLOW}Перезапуск контейнера с ботом...${NC}"
docker restart okypbot_app

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка перезапуска контейнера okypbot_app!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Контейнер okypbot_app успешно перезапущен${NC}"

# 5. Проверяем работоспособность
echo -e "${YELLOW}Проверка работоспособности (подождите 10 секунд для запуска сервисов)...${NC}"
sleep 10

# Проверяем доступность эндпоинта health
echo -e "${YELLOW}Проверка эндпоинта /health...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8080/health)

if [ $? -ne 0 ] || [ -z "$HEALTH_CHECK" ]; then
    echo -e "${RED}❌ Эндпоинт /health недоступен!${NC}"
else
    echo -e "${GREEN}✅ Эндпоинт /health доступен: $HEALTH_CHECK${NC}"
fi

# Проверяем доступность эндпоинта webhook
echo -e "${YELLOW}Проверка эндпоинта /okdesk-webhook (ожидаемый код: 405 Method Not Allowed)...${NC}"
WEBHOOK_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/okdesk-webhook)

if [ "$WEBHOOK_CHECK" == "405" ]; then
    echo -e "${GREEN}✅ Эндпоинт /okdesk-webhook доступен (код 405, т.к. требуется POST)${NC}"
else
    echo -e "${YELLOW}⚠️ Эндпоинт /okdesk-webhook вернул код $WEBHOOK_CHECK (ожидался 405)${NC}"
fi

echo -e "${BLUE}=== Скрипт завершен ===${NC}"
