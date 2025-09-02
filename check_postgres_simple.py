#!/usr/bin/env python3
"""
Простая проверка PostgreSQL через Docker без дополнительных зависимостей
"""

import subprocess
import sys
import json

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n🔍 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Успешно:")
            print(result.stdout)
        else:
            print(f"❌ Ошибка (код {result.returncode}):")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Тайм-аут команды")
        return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🐘 Проверка PostgreSQL в Docker")
    print("=" * 40)
    
    # Список проверок
    checks = [
        {
            "command": "docker-compose ps",
            "description": "Статус контейнеров"
        },
        {
            "command": "docker exec okypbot_postgres pg_isready -U postgres",
            "description": "Готовность PostgreSQL"
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -c "SELECT version();"',
            "description": "Версия PostgreSQL"
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -c "\\l"',
            "description": "Список баз данных"
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT current_database(), current_user;"',
            "description": "Подключение к базе okypbot"
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "\\dt"',
            "description": "Таблицы в базе okypbot"
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT \'PostgreSQL работает!\' as status;"',
            "description": "Тест простого запроса"
        }
    ]
    
    # Выполняем проверки
    success_count = 0
    for check in checks:
        if run_command(check["command"], check["description"]):
            success_count += 1
    
    # Итоги
    print(f"\n📊 Итоги проверки:")
    print(f"✅ Успешно: {success_count}/{len(checks)}")
    
    if success_count == len(checks):
        print("🎉 PostgreSQL полностью работоспособен!")
        return 0
    else:
        print("⚠️ Есть проблемы с PostgreSQL")
        return 1

if __name__ == "__main__":
    sys.exit(main())
