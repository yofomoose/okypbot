#!/usr/bin/env python3
# Скрипт для проверки совместимости версий компонентов системы

import os
import json
import sys
import subprocess
import platform
from datetime import datetime

# Определение цветов для вывода
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

# Функция для форматированного вывода
def print_colored(message, color):
    print(f"{color}{message}{Colors.RESET}")

# Получение информации о системе
def get_system_info():
    print_colored("Сбор информации о системе...", Colors.YELLOW)
    
    system_info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "python_version": platform.python_version(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Получение версии из git или файла
    git_version = "unknown"
    try:
        git_version = subprocess.check_output(["git", "describe", "--tags", "--always", "--dirty"]).decode().strip()
    except:
        if os.path.exists("version.txt"):
            with open("version.txt", "r") as f:
                git_version = f.read().strip()
    
    system_info["version"] = git_version
    
    return system_info

# Проверка зависимостей Python
def check_python_dependencies():
    print_colored("\nПроверка зависимостей Python...", Colors.YELLOW)
    
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print_colored(f"❌ Файл {requirements_file} не найден!", Colors.RED)
        return False
    
    # Чтение требуемых зависимостей
    with open(requirements_file, "r") as f:
        required = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"Найдено {len(required)} зависимостей в {requirements_file}")
    
    # Получение установленных пакетов
    try:
        installed = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode().split('\n')
        installed = [pkg.strip() for pkg in installed if pkg.strip()]
        
        # Преобразование в словарь для проверки
        installed_dict = {}
        for pkg in installed:
            if "==" in pkg:
                name, version = pkg.split("==", 1)
                installed_dict[name.lower()] = version
        
        # Проверка требуемых зависимостей
        missing = []
        outdated = []
        
        for req in required:
            if "==" in req:
                name, version = req.split("==", 1)
                name = name.lower()
                
                if name not in installed_dict:
                    missing.append(req)
                elif installed_dict[name] != version:
                    outdated.append((name, installed_dict[name], version))
            else:
                # Если версия не указана, просто проверяем наличие
                name = req.lower()
                if not any(name == pkg.lower() or name == pkg.lower().split("==")[0] for pkg in installed):
                    missing.append(req)
        
        # Вывод результатов
        if missing:
            print_colored(f"❌ Отсутствуют следующие зависимости:", Colors.RED)
            for pkg in missing:
                print(f"  - {pkg}")
        
        if outdated:
            print_colored(f"⚠️ Несоответствие версий зависимостей:", Colors.YELLOW)
            for name, installed_ver, required_ver in outdated:
                print(f"  - {name}: установлена {installed_ver}, требуется {required_ver}")
        
        if not missing and not outdated:
            print_colored("✅ Все зависимости установлены и соответствуют требованиям", Colors.GREEN)
            return True
        
        return len(missing) == 0
    
    except Exception as e:
        print_colored(f"❌ Ошибка при проверке зависимостей: {str(e)}", Colors.RED)
        return False

# Проверка конфигурации Docker
def check_docker_configuration():
    print_colored("\nПроверка конфигурации Docker...", Colors.YELLOW)
    
    # Проверка наличия Dockerfile
    if not os.path.exists("docker/Dockerfile"):
        print_colored("❌ Файл docker/Dockerfile не найден!", Colors.RED)
        return False
    
    # Проверка наличия docker-compose файла
    compose_file = "docker/docker-compose.prod.yml"
    if not os.path.exists(compose_file):
        print_colored(f"❌ Файл {compose_file} не найден!", Colors.RED)
        return False
    
    # Проверка содержимого docker-compose.yml
    with open(compose_file, "r") as f:
        content = f.read()
    
    # Проверка наличия основных сервисов
    required_services = ["bot", "postgres"]
    missing_services = []
    
    for service in required_services:
        if f"{service}:" not in content:
            missing_services.append(service)
    
    if missing_services:
        print_colored(f"❌ В {compose_file} отсутствуют следующие сервисы:", Colors.RED)
        for service in missing_services:
            print(f"  - {service}")
        return False
    
    # Проверка наличия volume для данных
    if "../database:/app/database" not in content:
        print_colored(f"⚠️ В {compose_file} отсутствует volume для директории database", Colors.YELLOW)
        print_colored("   Рекомендуется добавить volume для сохранения данных", Colors.YELLOW)
    else:
        print_colored("✅ Volume для директории database настроен", Colors.GREEN)
    
    print_colored("✅ Базовая конфигурация Docker корректна", Colors.GREEN)
    return True

# Проверка наличия ML модели
def check_ml_model():
    print_colored("\nПроверка ML модели...", Colors.YELLOW)
    
    # Проверка наличия директории
    if not os.path.exists("bot_model"):
        print_colored("❌ Директория bot_model не найдена!", Colors.RED)
        return False
    
    # Проверка наличия файлов модели
    required_files = ["classifier.pkl", "label_encoder.pkl", "model_metadata.json"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(f"bot_model/{file}"):
            missing_files.append(file)
    
    if missing_files:
        print_colored("❌ Отсутствуют следующие файлы модели:", Colors.RED)
        for file in missing_files:
            print(f"  - bot_model/{file}")
        return False
    
    # Проверка метаданных модели
    try:
        with open("bot_model/model_metadata.json", "r") as f:
            metadata = json.load(f)
        
        print_colored("✅ Информация о ML модели:", Colors.GREEN)
        print(f"  - Версия: {metadata.get('version', 'не указана')}")
        print(f"  - Дата обучения: {metadata.get('trained_date', 'не указана')}")
        print(f"  - Точность: {metadata.get('accuracy', 'не указана')}")
        print(f"  - Количество образцов: {metadata.get('samples_count', 'не указано')}")
        print(f"  - Количество категорий: {metadata.get('categories_count', 'не указано')}")
        
        # Проверка совместимости версии
        required_version = metadata.get('required_code_version')
        current_version = get_system_info().get('version')
        
        if required_version and current_version != "unknown" and required_version != current_version:
            print_colored(f"⚠️ Версия кода ({current_version}) не соответствует требуемой для модели ({required_version})", Colors.YELLOW)
            print_colored("   Возможны проблемы с работой ML классификатора", Colors.YELLOW)
        
        return True
    
    except Exception as e:
        print_colored(f"❌ Ошибка при чтении метаданных модели: {str(e)}", Colors.RED)
        return False

# Проверка структуры базы данных
def check_database_structure():
    print_colored("\nПроверка структуры базы данных...", Colors.YELLOW)
    
    # Проверка наличия файлов JSON базы данных
    json_db_files = ["database/users.json", "database/user_issues.json"]
    missing_files = []
    
    for file in json_db_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print_colored("⚠️ Отсутствуют следующие файлы базы данных:", Colors.YELLOW)
        for file in missing_files:
            print(f"  - {file}")
        print_colored("   Файлы будут созданы автоматически при первом запуске", Colors.YELLOW)
    else:
        # Проверка содержимого файлов
        valid_files = 0
        
        for file in json_db_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                print(f"  ✅ Файл {file} содержит {len(data) if isinstance(data, list) else 'корректные'} данные")
                valid_files += 1
            except json.JSONDecodeError:
                print_colored(f"❌ Файл {file} содержит некорректный JSON", Colors.RED)
            except Exception as e:
                print_colored(f"❌ Ошибка при чтении {file}: {str(e)}", Colors.RED)
        
        if valid_files == len(json_db_files):
            print_colored("✅ Все файлы базы данных корректны", Colors.GREEN)
    
    # Проверка модуля базы данных
    if os.path.exists("database/models.py"):
        print_colored("✅ Модуль models.py для работы с базой данных найден", Colors.GREEN)
    else:
        print_colored("❌ Отсутствует файл database/models.py", Colors.RED)
    
    # Проверка конфигурации базы данных
    if os.path.exists("config/db_config.py"):
        print_colored("✅ Файл конфигурации базы данных найден", Colors.GREEN)
    else:
        print_colored("❌ Отсутствует файл config/db_config.py", Colors.RED)
    
    return True

# Главная функция
def main():
    print_colored("🔍 ПРОВЕРКА СОВМЕСТИМОСТИ ВЕРСИЙ КОМПОНЕНТОВ СИСТЕМЫ", Colors.YELLOW)
    print("-" * 60)
    
    # Получение информации о системе
    system_info = get_system_info()
    
    print(f"Операционная система: {system_info['os']} {system_info['os_release']}")
    print(f"Версия Python: {system_info['python_version']}")
    print(f"Версия системы: {system_info['version']}")
    print(f"Дата проверки: {system_info['date']}")
    
    # Выполнение проверок
    checks = [
        ("Зависимости Python", check_python_dependencies),
        ("Конфигурация Docker", check_docker_configuration),
        ("ML модель", check_ml_model),
        ("Структура базы данных", check_database_structure)
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Вывод итогового результата
    print("\n" + "-" * 60)
    print_colored("РЕЗУЛЬТАТЫ ПРОВЕРКИ:", Colors.YELLOW)
    
    all_ok = True
    for name, result in results.items():
        status = "✅ OK" if result else "❌ ПРОБЛЕМЫ"
        status_color = Colors.GREEN if result else Colors.RED
        print(f"{name}: {status_color}{status}{Colors.RESET}")
        if not result:
            all_ok = False
    
    print("-" * 60)
    if all_ok:
        print_colored("✅ ВСЕ КОМПОНЕНТЫ СИСТЕМЫ СОВМЕСТИМЫ И ГОТОВЫ К РАБОТЕ", Colors.GREEN)
        return 0
    else:
        print_colored("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С СОВМЕСТИМОСТЬЮ КОМПОНЕНТОВ", Colors.YELLOW)
        print_colored("   Рекомендуется исправить обнаруженные проблемы перед запуском системы", Colors.YELLOW)
        return 1

if __name__ == "__main__":
    sys.exit(main())
