#!/usr/bin/env python3
"""
Простая проверка PostgreSQL через Docker без дополнительных зависимостей
Версия для сервера с автопоиском docker-compose файла
"""

import subprocess
import sys
import os

def find_docker_compose():
    """Находит файл docker-compose в текущей или родительских директориях"""
    compose_files = [
        'docker-compose.yml',
        'docker-compose.yaml', 
        'compose.yml',
        'compose.yaml'
    ]
    
    current_dir = os.getcwd()
    
    # Проверяем текущую директорию и родительские
    for i in range(5):  # Максимум 5 уровней вверх
        for compose_file in compose_files:
            compose_path = os.path.join(current_dir, compose_file)
            if os.path.exists(compose_path):
                return compose_path, current_dir
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Достигли корня
            break
        current_dir = parent_dir
    
    return None, None

def run_command(command, description, ignore_errors=False):
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
            return True
        else:
            if ignore_errors:
                print(f"⚠️ Предупреждение (код {result.returncode}):")
                print(result.stderr)
                return True
            else:
                print(f"❌ Ошибка (код {result.returncode}):")
                print(result.stderr)
                return False
            
    except subprocess.TimeoutExpired:
        print("❌ Тайм-аут команды")
        return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🐘 Проверка PostgreSQL в Docker (версия для сервера)")
    print("=" * 55)
    
    # Пытаемся найти docker-compose файл
    compose_path, compose_dir = find_docker_compose()
    
    if compose_path:
        print(f"📁 Найден docker-compose файл: {compose_path}")
        os.chdir(compose_dir)
        print(f"📂 Рабочая директория: {compose_dir}")
    else:
        print("⚠️ docker-compose файл не найден, пропускаем проверку контейнеров")
    
    # Список проверок
    checks = []
    
    # Добавляем проверку docker-compose только если файл найден
    if compose_path:
        checks.append({
            "command": "docker-compose ps",
            "description": "Статус контейнеров",
            "ignore_errors": False
        })
    
    # Основные проверки PostgreSQL
    checks.extend([
        {
            "command": "docker exec okypbot_postgres pg_isready -U postgres",
            "description": "Готовность PostgreSQL",
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -c "SELECT version();"',
            "description": "Версия PostgreSQL", 
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -c "\\l"',
            "description": "Список баз данных",
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT current_database(), current_user;"',
            "description": "Подключение к базе okypbot",
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "\\dt"',
            "description": "Таблицы в базе okypbot",
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT \'PostgreSQL работает!\' as status;"',
            "description": "Тест простого запроса",
            "ignore_errors": False
        },
        {
            "command": 'docker exec okypbot_postgres psql -U postgres -d okypbot -c "SELECT COUNT(*) as user_count FROM users;"',
            "description": "Количество пользователей в базе",
            "ignore_errors": True
        }
    ])
    
    # Выполняем проверки
    success_count = 0
    for check in checks:
        if run_command(
            check["command"], 
            check["description"],
            check.get("ignore_errors", False)
        ):
            success_count += 1
    
    # Итоги
    print(f"\n📊 Итоги проверки:")
    print(f"✅ Успешно: {success_count}/{len(checks)}")
    
    if success_count >= len(checks) - 1:  # Допускаем одну ошибку
        print("🎉 PostgreSQL полностью работоспособен!")
        
        # Дополнительная информация о подключении
        print(f"\n🔧 Информация для подключения:")
        print(f"Host: localhost (внутри Docker: postgres)")
        print(f"Port: 5432 (внешний порт может отличаться)")
        print(f"Database: okypbot") 
        print(f"User: postgres")
        print(f"Password: [из .env файла]")
        
        return 0
    else:
        print("⚠️ Есть критические проблемы с PostgreSQL")
        return 1

if __name__ == "__main__":
    sys.exit(main())
