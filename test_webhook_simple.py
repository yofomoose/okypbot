#!/usr/bin/env python3
"""
Простой скрипт для тестирования webhook с подписью
"""
import requests
import hmac
import hashlib
import json
import os
import sys

# Настройки
webhook_url = "https://okbot.teftelyatun.ru/okdesk-webhook"
webhook_secret = os.environ.get("OKDESK_WEBHOOK_SECRET", "test_secret")

# Если передан аргумент с ID заявки, используем его
issue_id = int(sys.argv[1]) if len(sys.argv) > 1 else 12345

# Данные для отправки
data = {
    "event": {
        "event_type": "new_comment"
    },
    "issue": {
        "id": issue_id
    },
    "comment": {
        "content": "Тестовый комментарий от webhook скрипта",
        "id": 67890,
        "is_public": True
    },
    "author": {
        "type": "employee",
        "first_name": "Test",
        "last_name": "User"
    }
}

# Создаем подпись
payload = json.dumps(data, separators=(',', ':')).encode('utf-8')
signature = hmac.new(
    webhook_secret.encode('utf-8'),
    payload,
    hashlib.sha256
).hexdigest()

# Отправляем запрос
headers = {
    'Content-Type': 'application/json',
    'X-Okdesk-Signature': f"sha256={signature}"
}

print(f"Отправка webhook запроса на {webhook_url}")
print(f"Тестируем заявку ID: {issue_id}")
print(f"Секрет для подписи: {webhook_secret}")

response = requests.post(webhook_url, json=data, headers=headers, verify=False)
print(f"\nСтатус: {response.status_code}")
print(f"Ответ: {response.text}")

# Проверяем логи
print("\nПроверьте логи на сервере командой:")
print("docker logs okypbot_app | grep webhook")
