# Config package
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Экспортируем основные настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
OKDESK_API_TOKEN = os.getenv("OKDESK_API_TOKEN")
OKDESK_BASE_URL = os.getenv("OKDESK_BASE_URL")

# Админы для ML обратной связи
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
    except ValueError:
        print("⚠️ Ошибка в настройке ADMIN_IDS в .env файле")
        ADMIN_IDS = []
