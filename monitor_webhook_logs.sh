#!/bin/bash
# Скрипт для мониторинга webhook логов в реальном времени

echo "🔍 Мониторинг webhook логов в реальном времени..."
echo "=================================================="
echo "Нажмите Ctrl+C для остановки мониторинга"
echo ""

# Мониторинг логов webhook сервера
if docker ps | grep -q okypbot_app; then
    echo "📡 Мониторинг логов webhook сервера:"
    docker logs -f okypbot_app 2>/dev/null | grep -i -E "(webhook|okdesk|signature|comment|issue)" || echo "❌ Нет webhook логов в данный момент"
else
    echo "❌ Контейнер okypbot_app не запущен"
fi

echo -e "\n✅ Мониторинг завершен!"
