# Config package
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Экспортируем основные настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
OKDESK_API_TOKEN = os.getenv("OKDESK_API_TOKEN")
OKDESK_BASE_URL = os.getenv("OKDESK_BASE_URL")
OKDESK_WEBHOOK_SECRET = os.getenv("OKDESK_WEBHOOK_SECRET", "")  # Секрет для проверки webhook подписи

# Webhook настройки
WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8001"))

# Настройки для Okdesk API
OKDESK_AUTHOR_ID = os.getenv("OKDESK_AUTHOR_ID")  # Фиксированный author_id для комментариев
if OKDESK_AUTHOR_ID:
    try:
        OKDESK_AUTHOR_ID = int(OKDESK_AUTHOR_ID)
    except ValueError:
        print("⚠️ Ошибка в настройке OKDESK_AUTHOR_ID в .env файле")
        OKDESK_AUTHOR_ID = None

# Админы для ML обратной связи
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
    except ValueError:
        print("⚠️ Ошибка в настройке ADMIN_IDS в .env файле")
        ADMIN_IDS = []
