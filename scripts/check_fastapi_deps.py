"""
Скрипт для проверки и установки необходимых зависимостей FastAPI и uvicorn
"""

import subprocess
import sys
import pkg_resources

def check_and_install_packages():
    """Проверяет наличие необходимых пакетов и устанавливает их при необходимости"""
    
    required_packages = {
        'fastapi': '0.103.1',  # Указываем конкретные версии для совместимости
        'uvicorn': '0.23.2',
        'pydantic': '2.3.0'
    }
    
    missing_packages = []
    
    print("Проверка необходимых зависимостей...")
    
    for package, version in required_packages.items():
        try:
            pkg_resources.require(f"{package}>={version}")
            print(f"✓ {package} (>= {version}) уже установлен")
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing_packages.append(f"{package}=={version}")
    
    if missing_packages:
        print(f"Отсутствуют необходимые пакеты: {', '.join(missing_packages)}")
        print("Установка пакетов...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✓ Все необходимые пакеты успешно установлены!")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при установке пакетов: {e}")
            return False
    else:
        print("✓ Все необходимые зависимости установлены!")
    
    return True

if __name__ == "__main__":
    if check_and_install_packages():
        print("Система готова для запуска FastAPI!")
    else:
        print("Ошибка при проверке/установке зависимостей.")
        sys.exit(1)
