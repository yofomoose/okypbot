#!/usr/bin/env python3
"""
Скрипт для быстрого исправления распространенных проблем в okypbot
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def fix_numpy_issue():
    """Исправляет проблему с numpy._core"""
    print("🔧 Исправление проблемы с numpy...")
    
    try:
        # Переустанавливаем numpy с правильной версией
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", 
            "numpy==1.25.2", "--force-reinstall"
        ], check=True)
        
        # Проверяем установку
        subprocess.run([
            sys.executable, "-c", 
            "import numpy; import numpy.core; print('✅ NumPy установлен правильно')"
        ], check=True)
        
        print("✅ Проблема с numpy исправлена")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при исправлении numpy: {e}")
        return False

def fix_file_permissions():
    """Исправляет проблемы с правами доступа к файлам"""
    print("🔧 Исправление прав доступа к файлам...")
    
    try:
        # Создаем необходимые директории
        directories = [
            "bot_model",
            "logs", 
            "data",
            "temp"
        ]
        
        for dir_name in directories:
            dir_path = Path(dir_name)
            dir_path.mkdir(exist_ok=True)
            
            # В Windows/Docker устанавливаем права
            if os.name != 'nt':  # Не Windows
                os.chmod(dir_path, 0o777)
        
        # Создаем файл training_examples.pkl если его нет
        training_file = Path("bot_model/training_examples.pkl")
        if not training_file.exists():
            import pickle
            with open(training_file, 'wb') as f:
                pickle.dump([], f)
            print("✅ Создан файл training_examples.pkl")
            
            if os.name != 'nt':
                os.chmod(training_file, 0o666)
        
        # Создаем альтернативную директорию во временной папке
        temp_dir = Path(tempfile.gettempdir()) / "okypbot_examples"
        temp_dir.mkdir(exist_ok=True)
        
        print("✅ Права доступа исправлены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении прав доступа: {e}")
        return False

def check_env_file():
    """Проверяет и исправляет .env файл"""
    print("🔧 Проверка .env файла...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден")
        print("Создайте .env файл с следующими переменными:")
        print("BOT_TOKEN=ваш_токен_бота")
        print("OKDESK_API_TOKEN=ваш_api_токен")
        print("OKDESK_BASE_URL=https://your-company.okdesk.ru")
        print("OKDESK_AUTHOR_ID=1")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_vars = ['BOT_TOKEN', 'OKDESK_API_TOKEN', 'OKDESK_BASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Отсутствуют переменные: {', '.join(missing_vars)}")
            
            # Добавляем недостающие переменные
            with open(env_path, 'a', encoding='utf-8') as f:
                f.write("\n# Добавлено автоматически:\n")
                for var in missing_vars:
                    if var == 'BOT_TOKEN':
                        f.write(f"{var}=YOUR_BOT_TOKEN_HERE\n")
                    elif var == 'OKDESK_API_TOKEN':
                        f.write(f"{var}=YOUR_OKDESK_API_TOKEN_HERE\n")
                    elif var == 'OKDESK_BASE_URL':
                        f.write(f"{var}=https://your-company.okdesk.ru\n")
            
            print("✅ Недостающие переменные добавлены в .env (требуется настройка)")
        else:
            print("✅ Все необходимые переменные присутствуют")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с .env: {e}")
        return False

def fix_docker_permissions():
    """Исправляет права в Docker контейнере"""
    print("🔧 Исправление Docker прав доступа...")
    
    try:
        # Проверяем, работаем ли мы в Docker
        if os.path.exists('/.dockerenv'):
            print("📦 Обнаружена работа в Docker контейнере")
            
            # Создаем директории с правильными правами
            os.system("mkdir -p /tmp/okypbot_examples")
            os.system("chmod 777 /tmp/okypbot_examples")
            os.system("chmod 777 bot_model/ 2>/dev/null || true")
            os.system("chmod 666 bot_model/*.pkl 2>/dev/null || true")
            
            print("✅ Права в Docker исправлены")
        else:
            print("ℹ️ Не обнаружена работа в Docker")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении Docker прав: {e}")
        return False

def reinstall_dependencies():
    """Переустанавливает зависимости с исправлениями"""
    print("🔧 Переустановка зависимостей...")
    
    try:
        # Обновляем pip
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        
        # Переустанавливаем критичные зависимости
        critical_packages = [
            "numpy==1.25.2",
            "scikit-learn==1.3.0",
            "aiogram==3.4.1",
            "aiohttp>=3.8.0"
        ]
        
        for package in critical_packages:
            print(f"Установка {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                package, "--force-reinstall"
            ], check=True)
        
        print("✅ Критичные зависимости переустановлены")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при переустановке зависимостей: {e}")
        return False

def main():
    """Основная функция исправления проблем"""
    
    print("🛠️ Okypbot - Исправление проблем")
    print("=" * 50)
    
    fixes_applied = []
    
    # 1. Проверяем .env файл
    if check_env_file():
        fixes_applied.append("✅ .env файл")
    else:
        fixes_applied.append("❌ .env файл")
    
    # 2. Исправляем права доступа
    if fix_file_permissions():
        fixes_applied.append("✅ Права доступа")
    else:
        fixes_applied.append("❌ Права доступа")
    
    # 3. Исправляем Docker права если нужно
    if fix_docker_permissions():
        fixes_applied.append("✅ Docker права")
    else:
        fixes_applied.append("❌ Docker права")
    
    # 4. Исправляем numpy
    if fix_numpy_issue():
        fixes_applied.append("✅ NumPy")
    else:
        fixes_applied.append("❌ NumPy")
    
    print("\n📋 Результаты исправлений:")
    for fix in fixes_applied:
        print(f"   {fix}")
    
    print("\n🚀 Следующие шаги:")
    print("1. Убедитесь что в .env файле установлены правильные значения")
    print("2. Запустите диагностику: python diagnose_okdesk.py")
    print("3. Перезапустите бота: python main.py")
    
    # Проверяем критичные импорты
    print("\n🔍 Проверка критичных импортов:")
    try:
        import numpy
        import numpy.core
        print("✅ NumPy работает")
    except ImportError as e:
        print(f"❌ NumPy не работает: {e}")
    
    try:
        import aiogram
        print("✅ Aiogram работает")
    except ImportError as e:
        print(f"❌ Aiogram не работает: {e}")
    
    try:
        import sklearn
        print("✅ Scikit-learn работает")
    except ImportError as e:
        print(f"❌ Scikit-learn не работает: {e}")

if __name__ == "__main__":
    main()
