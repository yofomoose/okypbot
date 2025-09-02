#!/usr/bin/env python
# Скрипт для очистки проекта перед публикацией в Git

import os
import shutil
import glob
import sys

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.RESET}")

# Конфигурация файлов и папок для удаления
TEMP_DIRS = [
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "build",
    "dist",
    ".ipynb_checkpoints",
    "venv-resave"
]

TEMP_FILES = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.class",
    "*.exe",
    "*.zip",
    "*.tar.gz",
    "*.log",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db"
]

# Дополнительные файлы которые можно считать лишними
REDUNDANT_FILES = [
    "Makefile.bak",
    "Makefile.new",
    "apply_all_fixes.sh",
    "check_db.py",
    "check_docker_config.ps1",
    "check_docker_status.sh",
    "check_production_status.sh",
    "check_training_data.py",
    "check_training_examples.py",
    "create_new_model.py",
    "debug_categories.py",
    "deploy_production.sh", 
    "deploy-full.sh",
    "deploy.sh",
    "final_system_test.sh",
    "fix_aiogram_config.py",
    "fix_container_aiogram.py",
    "fix_database_issues.py",
    "fix_ml_model.py", 
    "fix_system_issues.sh",
    "monitor_webhook_logs.sh",
    "test_aiogram.py",
    "test_bot_model_integration.py", 
    "test_fixed_model.py",
    "test_ml_training_extended.py",
    "test_ml_training.py", 
    "test_okdesk_connection.py",
    "test_webhook.py",
    "train_on_new_data_fixed.py",
    "train_on_new_data.py",
    "update-bot.sh"
]

# Файлы документации которые можно безопасно оставить
IMPORTANT_DOCS = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "DATABASE_README.md",
    "DEPLOYMENT_GUIDE.md"
]

# Дублирующиеся файлы в корне, которые есть в поддиректориях
DUPLICATE_FILES = [
    "deployment/deploy.sh",
    "deployment/deploy-full.sh",
    "deployment/update-bot.sh",
    "docker/check_docker_config.ps1"
]

def find_files_to_clean(base_dir="."):
    """Находит файлы, которые следует удалить"""
    files_to_remove = []
    dirs_to_remove = []
    
    # Поиск временных директорий
    for temp_dir_pattern in TEMP_DIRS:
        for folder_path in glob.glob(os.path.join(base_dir, "**", temp_dir_pattern), recursive=True):
            if os.path.isdir(folder_path):
                dirs_to_remove.append(folder_path)
    
    # Поиск временных файлов
    for temp_file_pattern in TEMP_FILES:
        for file_path in glob.glob(os.path.join(base_dir, "**", temp_file_pattern), recursive=True):
            if os.path.isfile(file_path):
                files_to_remove.append(file_path)
    
    # Добавление резервных копий файлов
    for file_path in glob.glob(os.path.join(base_dir, "**", "*~"), recursive=True):
        if os.path.isfile(file_path):
            files_to_remove.append(file_path)
    
    # Проверка лишних файлов
    for redundant_file in REDUNDANT_FILES:
        file_path = os.path.join(base_dir, redundant_file)
        if os.path.isfile(file_path):
            files_to_remove.append(file_path)
    
    return files_to_remove, dirs_to_remove

def clean_files(files_list, dirs_list, dry_run=True):
    """Удаляет файлы и директории из списков"""
    print_colored("\n🧹 Начинаем очистку проекта...", Colors.YELLOW)
    
    # Подсчет общего размера удаляемых файлов
    total_size = 0
    for file_path in files_list:
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    for dir_path in dirs_list:
        if os.path.exists(dir_path):
            for dirpath, _, filenames in os.walk(dir_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
    
    # Вывод информации о файлах
    if files_list:
        print_colored(f"\n📄 Файлы для удаления ({len(files_list)}):", Colors.YELLOW)
        for file_path in sorted(files_list):
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  - {file_path} ({size/1024:.1f} KB)")
            else:
                print(f"  - {file_path} (не найден)")
    
    # Вывод информации о директориях
    if dirs_list:
        print_colored(f"\n📁 Директории для удаления ({len(dirs_list)}):", Colors.YELLOW)
        for dir_path in sorted(dirs_list):
            print(f"  - {dir_path}")
    
    # Выводим итоговый размер
    print_colored(f"\n💾 Общий объем освобождаемого места: {total_size/1024/1024:.2f} MB", Colors.GREEN)
    
    # Если это не тестовый запуск, выполняем удаление
    if not dry_run:
        if input("\n⚠️ Вы действительно хотите удалить эти файлы? (y/n): ").lower() == "y":
            # Удаление файлов
            for file_path in files_list:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Удален файл: {file_path}")
                except Exception as e:
                    print_colored(f"Ошибка при удалении {file_path}: {str(e)}", Colors.RED)
            
            # Удаление директорий
            for dir_path in dirs_list:
                try:
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path)
                        print(f"Удалена директория: {dir_path}")
                except Exception as e:
                    print_colored(f"Ошибка при удалении {dir_path}: {str(e)}", Colors.RED)
            
            print_colored("\n✅ Очистка завершена успешно!", Colors.GREEN)
        else:
            print_colored("\n❌ Операция отменена пользователем", Colors.YELLOW)
    else:
        print_colored("\nℹ️ Это тестовый запуск. Файлы не были удалены.", Colors.YELLOW)
        print_colored("Для удаления файлов запустите скрипт с параметром --clean", Colors.YELLOW)

def create_gitignore():
    """Создаёт или обновляет .gitignore файл"""
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so
*.dll
*.dylib

# Distribution / packaging
dist/
build/
*.egg-info/

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
coverage.xml
*.cover

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# virtualenv
venv/
env/
ENV/
venv-resave/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# VS Code
.vscode/
*.code-workspace

# PyCharm
.idea/
*.iml
*.iws
*.ipr

# Database
*.sqlite3
*.db-journal

# Backups
backups/
database_backup/
*.bak

# Local configuration
.env
.env.local

# Logs
logs/

# Temporary files
tmp/
temp/
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print_colored("\n✅ Файл .gitignore создан/обновлен", Colors.GREEN)

def main():
    print_colored("🧹 ОЧИСТКА ПРОЕКТА ПЕРЕД ПУБЛИКАЦИЕЙ В GIT", Colors.GREEN)
    print("-" * 60)
    
    # Определяем режим запуска
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        dry_run = False
    
    # Ищем файлы для удаления
    files_to_remove, dirs_to_remove = find_files_to_clean()
    
    # Удаляем найденные файлы
    clean_files(files_to_remove, dirs_to_remove, dry_run)
    
    # Создаем .gitignore
    create_gitignore()
    
    if dry_run:
        print_colored("\nℹ️ Запустите скрипт с параметром --clean для выполнения очистки:", Colors.YELLOW)
        print_colored("    python clean_repo.py --clean", Colors.YELLOW)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
