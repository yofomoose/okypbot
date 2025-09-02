#!/usr/bin/env python3
"""
Скрипт для проверки подключения к PostgreSQL
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_postgres_connection():
    """Проверка подключения к PostgreSQL"""
    
    # Параметры подключения
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "okypbot")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    
    print("🔍 Проверка подключения к PostgreSQL")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    
    try:
        # Пытаемся подключиться
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Проверяем подключение
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("\n✅ Подключение успешно!")
        print(f"📊 Версия PostgreSQL: {db_version[0]}")
        
        # Проверяем таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️ Таблицы не найдены (база данных пустая)")
        
        cursor.close()
        connection.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Ошибка подключения: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Проверьте правильность параметров подключения в .env")
        print("2. Убедитесь что PostgreSQL запущен")
        print("3. Проверьте сетевое подключение")
        print("4. Проверьте права доступа пользователя")
        return False
        
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False

def check_docker_postgres():
    """Проверка PostgreSQL в Docker"""
    print("\n🐳 Проверка PostgreSQL в Docker")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Проверяем статус контейнера
        result = subprocess.run([
            "docker", "ps", "--filter", "name=okypbot_postgres", "--format", "table {{.Names}}\t{{.Status}}"
        ], capture_output=True, text=True, check=True)
        
        if "okypbot_postgres" in result.stdout:
            print("✅ Контейнер PostgreSQL запущен")
            print(result.stdout)
            
            # Проверяем логи контейнера
            logs_result = subprocess.run([
                "docker", "logs", "--tail", "10", "okypbot_postgres"
            ], capture_output=True, text=True)
            
            if logs_result.stdout:
                print("\n📋 Последние логи PostgreSQL:")
                print(logs_result.stdout)
                
            if logs_result.stderr:
                print("\n⚠️ Ошибки в логах:")
                print(logs_result.stderr)
                
        else:
            print("❌ Контейнер PostgreSQL не найден или не запущен")
            print("\n🚀 Запустите контейнер:")
            print("docker-compose up -d postgres")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения Docker команды: {e}")
    except FileNotFoundError:
        print("❌ Docker не найден. Убедитесь что Docker установлен.")

def reset_postgres_password():
    """Сброс пароля PostgreSQL"""
    print("\n🔄 Сброс пароля PostgreSQL")
    print("=" * 50)
    
    password = os.getenv("DB_PASSWORD", "postgres")
    
    commands = [
        f'docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD \'{password}\';"',
        'docker restart okypbot_postgres'
    ]
    
    print("Выполните следующие команды:")
    for cmd in commands:
        print(f"  {cmd}")

def main():
    """Основная функция"""
    print("🐘 PostgreSQL Connection Checker")
    print("Версия: 1.0.0")
    print("=" * 50)
    
    # Проверяем переменные окружения
    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Добавьте их в .env файл")
        return
    
    # Основная проверка подключения
    success = check_postgres_connection()
    
    if not success:
        # Дополнительные проверки для Docker
        check_docker_postgres()
        reset_postgres_password()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PostgreSQL готов к работе!")
    else:
        print("💡 Следуйте инструкциям выше для решения проблем")

if __name__ == "__main__":
    main()
