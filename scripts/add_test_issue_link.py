#!/usr/bin/env python3
"""
Скрипт для добавления тестовой связи между заявкой и пользователем
"""
import asyncio
import sys
import json

async def add_test_issue_user_link(issue_id, user_id):
    # Импортируем необходимые модули
    try:
        from database.models import db
    except ImportError:
        print("Ошибка: не удалось импортировать модули базы данных")
        return
    
    # Проверяем наличие пользователя
    user = db.get_user(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден")
        print("Существующие пользователи:")
        for uid, user in db.users.items():
            print(f"  - ID: {uid}, Имя: {user.full_name}")
        return
    
    print(f"Добавляем связь между заявкой {issue_id} и пользователем {user_id} ({user.full_name})")
    
    # Добавляем связь
    await db.add_user_issue_for_monitoring(issue_id, user_id)
    print(f"✅ Связь добавлена успешно")
    
    # Выводим все активные связи
    print("\nАктивные связи заявок с пользователями:")
    active_issues = await db.get_active_user_issues()
    if not active_issues:
        print("  - Нет активных связей")
    else:
        for issue in active_issues:
            print(f"  - Заявка: {issue['issue_id']}, Пользователь: {issue['user_id']}")

def print_usage():
    print("Использование: python add_test_issue_link.py <ID заявки> <ID пользователя в Telegram>")
    print("Пример: python add_test_issue_link.py 12345 987654321")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    try:
        issue_id = int(sys.argv[1])
        user_id = int(sys.argv[2])
        asyncio.run(add_test_issue_user_link(issue_id, user_id))
    except ValueError:
        print("Ошибка: ID заявки и ID пользователя должны быть целыми числами")
        print_usage()
        sys.exit(1)
