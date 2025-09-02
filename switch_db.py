#!/usr/bin/env python3
"""
Скрипт для переключения между PostgreSQL и SQLite
"""

import os
import sys
from pathlib import Path

def switch_to_sqlite():
    """Переключает приложение на использование SQLite"""
    
    print("🔄 Переключение на SQLite базу данных")
    print("=" * 50)
    
    # Читаем текущий .env файл
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Обновляем настройки базы данных
    new_lines = []
    for line in lines:
        if line.startswith("DB_HOST="):
            new_lines.append("# DB_HOST=postgres  # Отключено для SQLite\n")
        elif line.startswith("DB_PORT="):
            new_lines.append("# DB_PORT=5432     # Отключено для SQLite\n")
        elif line.startswith("DB_NAME="):
            new_lines.append("# DB_NAME=okypbot  # Отключено для SQLite\n")
        elif line.startswith("DB_USER="):
            new_lines.append("# DB_USER=postgres # Отключено для SQLite\n")
        elif line.startswith("DB_PASSWORD="):
            new_lines.append("# DB_PASSWORD=Cnhjywsq97 # Отключено для SQLite\n")
        else:
            new_lines.append(line)
    
    # Добавляем настройку для SQLite
    new_lines.append("\n# SQLite Configuration (активно)\n")
    new_lines.append("USE_SQLITE=true\n")
    new_lines.append("SQLITE_DB_PATH=okypbot.db\n")
    
    # Сохраняем обновленный .env файл
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Настройки обновлены для использования SQLite")
    print("📂 База данных будет создана в файле: okypbot.db")
    return True

def switch_to_postgres():
    """Переключает приложение на использование PostgreSQL"""
    
    print("🔄 Переключение на PostgreSQL базу данных")
    print("=" * 50)
    
    # Читаем текущий .env файл
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Обновляем настройки базы данных
    new_lines = []
    skip_sqlite = False
    
    for line in lines:
        if "SQLite Configuration" in line:
            skip_sqlite = True
            continue
        elif skip_sqlite and (line.startswith("USE_SQLITE=") or line.startswith("SQLITE_DB_PATH=")):
            continue
        elif line.startswith("# DB_HOST="):
            new_lines.append("DB_HOST=postgres\n")
        elif line.startswith("# DB_PORT="):
            new_lines.append("DB_PORT=5432\n")
        elif line.startswith("# DB_NAME="):
            new_lines.append("DB_NAME=okypbot\n")
        elif line.startswith("# DB_USER="):
            new_lines.append("DB_USER=postgres\n")
        elif line.startswith("# DB_PASSWORD="):
            new_lines.append("DB_PASSWORD=Cnhjywsq97\n")
        else:
            new_lines.append(line)
            skip_sqlite = False
    
    # Сохраняем обновленный .env файл
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Настройки обновлены для использования PostgreSQL")
    return True

def check_current_db():
    """Проверяет какая база данных сейчас используется"""
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    
    print("📊 Текущая конфигурация базы данных")
    print("=" * 50)
    
    if use_sqlite:
        sqlite_path = os.getenv("SQLITE_DB_PATH", "okypbot.db")
        print(f"🗃️ Используется: SQLite")
        print(f"📂 Файл: {sqlite_path}")
        
        if Path(sqlite_path).exists():
            size = Path(sqlite_path).stat().st_size
            print(f"💾 Размер: {size} байт")
        else:
            print("⚠️ Файл базы данных не существует (будет создан при первом запуске)")
    else:
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "okypbot")
        
        print(f"🐘 Используется: PostgreSQL")
        print(f"🌐 Хост: {db_host}:{db_port}")
        print(f"📋 База: {db_name}")

def main():
    """Основная функция"""
    
    if len(sys.argv) < 2:
        print("🗃️ Database Switcher")
        print("=" * 50)
        print("Использование:")
        print("  python switch_db.py sqlite     - переключиться на SQLite")
        print("  python switch_db.py postgres   - переключиться на PostgreSQL")
        print("  python switch_db.py status     - показать текущую конфигурацию")
        return
    
    command = sys.argv[1].lower()
    
    if command == "sqlite":
        success = switch_to_sqlite()
        if success:
            print("\n🚀 Теперь можно запускать приложение с SQLite!")
            print("python main.py")
    
    elif command == "postgres":
        success = switch_to_postgres()
        if success:
            print("\n🚀 Теперь можно запускать приложение с PostgreSQL!")
            print("Убедитесь что PostgreSQL запущен:")
            print("docker-compose up -d postgres")
    
    elif command == "status":
        check_current_db()
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: sqlite, postgres, status")

if __name__ == "__main__":
    main()
