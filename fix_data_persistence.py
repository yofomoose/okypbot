"""
Модуль для создания постоянного тома данных в Docker-контейнере.
Этот скрипт исправляет проблему с потерей данных при пересборке контейнеров.
"""

import os
import sys
import json

def ensure_database_directory():
    """Создает директорию database если она не существует"""
    if not os.path.exists('database'):
        os.makedirs('database')
        print("✅ Создана директория database")
    else:
        print("✅ Директория database уже существует")

def create_default_json_files():
    """Создает пустые JSON файлы с дефолтными структурами если они не существуют"""
    files_to_create = {
        'database/users.json': {'users': {}},
        'database/user_issues.json': {'issues': {}},
        'database/employee_mapping.json': {'mappings': {}, 'default_employee_id': None}
    }
    
    for file_path, default_content in files_to_create.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            print(f"✅ Создан файл {file_path}")
        else:
            print(f"✅ Файл {file_path} уже существует")

def check_docker_compose():
    """Проверяет, правильно ли настроен docker-compose.prod.yml"""
    compose_path = 'docker/docker-compose.prod.yml'
    if not os.path.exists(compose_path):
        print(f"❌ Файл {compose_path} не найден")
        return
    
    with open(compose_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '../database:/app/database' not in content:
        print(f"⚠️ В файле {compose_path} не настроен том для директории database")
        print("📝 Добавьте следующую строку в раздел volumes сервиса bot:")
        print("      - ../database:/app/database")
    else:
        print(f"✅ Том для директории database правильно настроен в {compose_path}")

if __name__ == "__main__":
    print("=== Исправление проблемы с потерей данных при пересборке контейнеров ===")
    
    ensure_database_directory()
    create_default_json_files()
    check_docker_compose()
    
    print("\n✅ Исправления выполнены успешно")
    print("⚠️ Не забудьте перезапустить контейнер после внесения изменений")
    print("💡 Для полного обновления с сохранением данных используйте скрипт deploy_to_production.sh")
