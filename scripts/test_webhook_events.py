"""
Скрипт для тестирования вебхука с различными типами событий
"""
import requests
import json
import hmac
import hashlib
import sys
import os
from datetime import datetime

# Укажите адрес сервера
SERVER_URL = "http://localhost:8080"

# Функция для вычисления подписи
def calculate_signature(payload, secret):
    if not secret:
        return ""
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"

# Функция для отправки тестового события
def send_test_event(event_type, secret=""):
    # Создаем тестовые данные в зависимости от типа события
    if event_type == "new_comment":
        data = {
            "event": {
                "event_type": "new_comment",
                "comment": {
                    "id": 123456,
                    "content": "Это тестовый комментарий для проверки вебхука",
                    "is_public": True
                },
                "author": {
                    "type": "employee",
                    "first_name": "Тестовый",
                    "last_name": "Специалист"
                }
            },
            "issue": {
                "id": 12345
            }
        }
    elif event_type == "status_changed":
        data = {
            "event": {
                "event_type": "status_changed",
                "old_status": {
                    "code": "new",
                    "name": "Новая"
                },
                "new_status": {
                    "code": "in_progress",
                    "name": "В работе"
                }
            },
            "issue": {
                "id": 12345
            }
        }
    elif event_type == "assignee_changed":
        data = {
            "event": {
                "event_type": "assignee_changed",
                "new_assignee": {
                    "id": 789,
                    "first_name": "Новый",
                    "last_name": "Специалист"
                }
            },
            "issue": {
                "id": 12345
            }
        }
    else:
        data = {
            "event": {
                "event_type": event_type
            },
            "issue": {
                "id": 12345
            }
        }
    
    # Преобразуем данные в JSON
    payload = json.dumps(data)
    
    # Вычисляем подпись
    signature = calculate_signature(payload, secret)
    
    # Заголовки запроса
    headers = {
        "Content-Type": "application/json"
    }
    
    if signature:
        headers["X-Okdesk-Signature"] = signature
    
    # Выводим информацию о запросе
    print(f"Отправка {event_type} на {SERVER_URL}/okdesk-webhook")
    print(f"Данные: {payload}")
    if signature:
        print(f"Подпись: {signature}")
    
    # Отправляем запрос
    try:
        response = requests.post(
            f"{SERVER_URL}/okdesk-webhook",
            headers=headers,
            data=payload
        )
        
        # Выводим результат
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        return response.status_code == 200
    
    except Exception as e:
        print(f"Ошибка при отправке запроса: {e}")
        return False

def main():
    # Проверяем аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование: python test_webhook_events.py [event_type] [secret]")
        print("Доступные типы событий: new_comment, status_changed, assignee_changed, test")
        return
    
    event_type = sys.argv[1]
    secret = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print(f"=== Тестирование вебхука {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    success = send_test_event(event_type, secret)
    
    if success:
        print("✅ Тест успешно завершен!")
    else:
        print("❌ Тест завершен с ошибкой!")

if __name__ == "__main__":
    main()
