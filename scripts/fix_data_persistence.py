"""
Модуль для исправления проблемы с монтированием томов в Docker
"""

import os
import json
import shutil
from pathlib import Path

def ensure_data_directories():
    """
    Создает необходимые директории для данных и
    копирует существующие данные в правильные места
    """
    # Директории, которые должны существовать
    data_dirs = [
        "database",
        "ml",
        "bot_model",
        "logs",
        "data"
    ]
    
    # Создаем директории, если они не существуют
    for dir_name in data_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    # Пути к файлам данных в корне проекта
    database_files = [
        ("database/users.json", {"users": {}}),
        ("database/user_issues.json", {"issues": {}}),
        ("database/employee_mapping.json", {"mappings": {}, "default_employee_id": None})
    ]
    
    # Создаем файлы данных с дефолтными значениями, если они не существуют
    for file_path, default_data in database_files:
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                print(f"✅ Создан файл {file_path}")
            except Exception as e:
                print(f"❌ Ошибка создания файла {file_path}: {e}")
    
    print("✅ Структура директорий проверена и исправлена")

def check_docker_volumes():
    """
    Проверяет настройки томов в docker-compose.prod.yml
    """
    docker_compose_path = "docker/docker-compose.prod.yml"
    
    if not os.path.exists(docker_compose_path):
        print(f"❌ Файл {docker_compose_path} не найден")
        return
    
    try:
        with open(docker_compose_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие необходимых томов
        required_volumes = [
            "database_data:/app/database",
            "ml_data:/app/ml",
            "bot_logs:/app/logs",
            "bot_data:/app/data"
        ]
        
        missing_volumes = []
        for volume in required_volumes:
            if volume not in content:
                missing_volumes.append(volume)
        
        if missing_volumes:
            print("⚠️ Обнаружены отсутствующие тома в docker-compose.prod.yml:")
            for volume in missing_volumes:
                print(f"  - {volume}")
            
            print("\nРекомендуется добавить следующие тома в секцию volumes сервиса bot:")
            for volume in missing_volumes:
                print(f"      - {volume}")
        else:
            print("✅ Все необходимые тома настроены в docker-compose.prod.yml")
    
    except Exception as e:
        print(f"❌ Ошибка проверки docker-compose.prod.yml: {e}")

if __name__ == "__main__":
    print("🔧 Проверка и исправление структуры данных проекта...")
    ensure_data_directories()
    check_docker_volumes()
    print("✅ Готово!")
