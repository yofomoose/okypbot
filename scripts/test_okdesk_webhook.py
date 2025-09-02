"""
Скрипт для тестирования веб-хука OkDesk
"""
import requests
import json
import argparse
from pprint import pprint

def test_webhook(url, event_type):
    """
    Отправляет тестовый вебхук с выбранным типом события
    
    Args:
        url: URL вебхука
        event_type: Тип события (new_comment, status_changed, assignee_changed)
    """
    # Подготавливаем тестовые данные в зависимости от типа события
    if event_type == "new_comment":
        data = {
            "event": {
                "event_type": "new_comment",
                "comment": {
                    "id": 123456,
                    "content": "Тестовый комментарий для проверки вебхука",
                    "is_public": True
                },
                "author": {
                    "type": "employee",  # employee или contact
                    "first_name": "Тест",
                    "last_name": "Специалист"
                }
            },
            "issue": {
                "id": 12345,
                "number": "TEST-12345",
                "subject": "Тестовая заявка"
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
                "id": 12345,
                "number": "TEST-12345",
                "subject": "Тестовая заявка"
            }
        }
    elif event_type == "assignee_changed":
        data = {
            "event": {
                "event_type": "assignee_changed",
                "new_assignee": {
                    "id": 789,
                    "first_name": "Новый",
                    "last_name": "Исполнитель"
                }
            },
            "issue": {
                "id": 12345,
                "number": "TEST-12345",
                "subject": "Тестовая заявка"
            }
        }
    else:
        print(f"Неизвестный тип события: {event_type}")
        print("Поддерживаемые типы: new_comment, status_changed, assignee_changed")
        return
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Отправка {event_type} на {url}...")
    print("\nТело запроса:")
    pprint(data)
    print("\nОтправка запроса...")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=data
        )
        
        print(f"\nСтатус ответа: {response.status_code}")
        print("Заголовки ответа:")
        pprint(dict(response.headers))
        print("\nТело ответа:")
        try:
            pprint(response.json())
        except:
            print(response.text)
        
        if response.status_code == 200:
            print("\n✅ Запрос успешно обработан!")
        else:
            print(f"\n❌ Ошибка! Код ответа: {response.status_code}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при отправке запроса: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Тестирование вебхука OkDesk")
    parser.add_argument("url", help="URL вебхука для тестирования")
    parser.add_argument("event_type", choices=["new_comment", "status_changed", "assignee_changed"],
                        help="Тип события для тестирования")
    
    args = parser.parse_args()
    test_webhook(args.url, args.event_type)
