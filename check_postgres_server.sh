#!/bin/bash

echo "🔍 Проверка подключения к PostgreSQL на сервере"
echo "=============================================="
echo "⏰ Время: $(date)"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. Проверяем статус Docker контейнеров
echo -e "${CYAN}🐳 Статус Docker контейнеров:${NC}"
docker-compose ps
echo ""

# 2. Проверяем логи PostgreSQL (последние 20 строк)
echo -e "${CYAN}📋 Последние логи PostgreSQL:${NC}"
docker-compose logs --tail=20 postgres
echo ""

# 3. Проверяем подключение к PostgreSQL изнутри контейнера
echo -e "${CYAN}🔗 Проверка подключения изнутри контейнера:${NC}"
if docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 'PostgreSQL работает!' as status, version();" 2>/dev/null; then
    echo -e "${GREEN}✅ PostgreSQL доступен изнутри контейнера${NC}"
else
    echo -e "${RED}❌ Ошибка подключения изнутри контейнера${NC}"
fi
echo ""

# 4. Проверяем таблицы в базе данных
echo -e "${CYAN}📊 Таблицы в базе данных:${NC}"
if docker exec okypbot_postgres psql -U postgres -d okypbot -c "\dt" 2>/dev/null; then
    echo -e "${GREEN}✅ Таблицы получены${NC}"
else
    echo -e "${YELLOW}⚠️ Таблицы не найдены или ошибка доступа${NC}"
fi
echo ""

# 5. Проверяем подключение с хоста
echo -e "${CYAN}🌐 Проверка подключения с хоста (порт 5433):${NC}"
if command -v psql >/dev/null 2>&1; then
    if PGPASSWORD=Cnhjywsq97 psql -h localhost -p 5433 -U postgres -d okypbot -c "SELECT 'Подключение с хоста работает!' as status;" 2>/dev/null; then
        echo -e "${GREEN}✅ Подключение с хоста работает${NC}"
    else
        echo -e "${RED}❌ Ошибка подключения с хоста${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ psql не установлен на хосте${NC}"
fi
echo ""

# 6. Проверяем сетевые порты
echo -e "${CYAN}🔌 Проверка сетевых портов:${NC}"
if command -v netstat >/dev/null 2>&1; then
    echo "Порты PostgreSQL:"
    netstat -tlnp | grep :543
elif command -v ss >/dev/null 2>&1; then
    echo "Порты PostgreSQL:"
    ss -tlnp | grep :543
else
    echo -e "${YELLOW}⚠️ netstat и ss не доступны${NC}"
fi
echo ""

# 7. Проверяем использование ресурсов
echo -e "${CYAN}📈 Использование ресурсов контейнером PostgreSQL:${NC}"
docker stats okypbot_postgres --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo -e "${YELLOW}⚠️ Статистика недоступна${NC}"
echo ""

# 8. Проверяем переменные окружения
echo -e "${CYAN}🔧 Переменные окружения PostgreSQL:${NC}"
docker exec okypbot_postgres env | grep POSTGRES
echo ""

# 9. Проверяем место на диске
echo -e "${CYAN}💾 Использование диска:${NC}"
df -h /var/lib/docker 2>/dev/null || df -h /
echo ""

# Итоговый отчет
echo -e "${CYAN}📊 ИТОГИ ПРОВЕРКИ:${NC}"
echo "========================"

# Проверяем, запущен ли контейнер
if docker ps | grep -q okypbot_postgres; then
    echo -e "${GREEN}✅ Контейнер PostgreSQL запущен${NC}"
    
    # Проверяем подключение
    if docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL доступен и работает${NC}"
        echo -e "${GREEN}🎉 Все проверки пройдены успешно!${NC}"
    else
        echo -e "${RED}❌ PostgreSQL запущен, но недоступен${NC}"
        echo -e "${YELLOW}🔧 Рекомендация: Проверьте логи и перезапустите контейнер${NC}"
    fi
else
    echo -e "${RED}❌ Контейнер PostgreSQL не запущен${NC}"
    echo -e "${YELLOW}🔧 Рекомендация: Запустите контейнеры командой 'docker-compose up -d'${NC}"
fi

echo ""
echo -e "${CYAN}🔧 Полезные команды для диагностики:${NC}"
echo "docker-compose logs postgres           # Полные логи PostgreSQL"
echo "docker exec -it okypbot_postgres bash  # Вход в контейнер"
echo "docker-compose restart postgres        # Перезапуск PostgreSQL"
echo "docker-compose down && docker-compose up -d  # Полный перезапуск"
