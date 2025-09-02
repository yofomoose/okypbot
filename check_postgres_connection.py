#!/usr/bin/env python3
"""
Скрипт для проверки подключения к PostgreSQL
Работает как локально, так и на сервере
"""

import os
import sys
import psycopg2
from datetime import datetime
import subprocess

def load_env_file(env_file=".env"):
    """Загружает переменные из .env файла"""
    env_vars = {}
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"⚠️ Файл {env_file} не найден")
    return env_vars

def check_docker_postgres():
    """Проверяет PostgreSQL через Docker"""
    print("🐳 Проверка PostgreSQL через Docker...")
    
    try:
        # Проверяем статус контейнера
        result = subprocess.run(['docker', 'ps', '--filter', 'name=postgres', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Статус PostgreSQL контейнера:")
            print(result.stdout)
        
        # Проверяем подключение изнутри контейнера
        cmd = ['docker', 'exec', 'okypbot_postgres', 'psql', '-U', 'postgres', '-d', 'okypbot', '-c', 'SELECT version();']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Подключение к PostgreSQL через Docker успешно!")
            print("📊 Версия PostgreSQL:")
            print(result.stdout)
            return True
        else:
            print("❌ Ошибка подключения через Docker:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке Docker: {e}")
        return False

def check_direct_postgres(host, port, database, username, password):
    """Прямая проверка подключения к PostgreSQL"""
    print(f"🔗 Прямое подключение к PostgreSQL {host}:{port}...")
    
    try:
        # Попытка подключения
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Проверяем версию
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Прямое подключение успешно!")
        print(f"📊 Версия: {version}")
        
        # Проверяем таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("📋 Таблицы в базе данных:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("ℹ️ Таблицы в базе данных отсутствуют")
        
        # Проверяем права пользователя
        cursor.execute("SELECT current_user, session_user;")
        user_info = cursor.fetchone()
        print(f"👤 Текущий пользователь: {user_info[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def check_environment_variables():
    """Проверяет переменные окружения"""
    print("🔧 Проверка переменных окружения...")
    
    # Загружаем из .env файла
    env_vars = load_env_file()
    
    # Проверяем системные переменные
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    
    config = {}
    missing_vars = []
    
    for var in required_vars:
        # Сначала проверяем системные переменные
        value = os.getenv(var)
        if not value:
            # Потом проверяем .env файл
            value = env_vars.get(var)
        
        if value:
            config[var] = value
            # Скрываем пароль в выводе
            display_value = "***" if 'PASSWORD' in var else value
            print(f"  ✅ {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f"  ❌ {var}: не найден")
    
    if missing_vars:
        print(f"⚠️ Отсутствуют переменные: {', '.join(missing_vars)}")
        return None
    
    return config

def main():
    print("🔍 Проверка подключения к PostgreSQL")
    print("=" * 50)
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Проверяем переменные окружения
    config = check_environment_variables()
    print()
    
    if not config:
        print("❌ Не удается получить конфигурацию базы данных")
        return False
    
    # 2. Проверяем через Docker (если доступен)
    docker_success = check_docker_postgres()
    print()
    
    # 3. Прямое подключение
    direct_success = check_direct_postgres(
        host=config['DB_HOST'],
        port=config['DB_PORT'],
        database=config['DB_NAME'],
        username=config['DB_USER'],
        password=config['DB_PASSWORD']
    )
    print()
    
    # Итоговый результат
    print("📊 ИТОГИ ПРОВЕРКИ:")
    print("=" * 30)
    print(f"🐳 Docker подключение: {'✅ Успешно' if docker_success else '❌ Ошибка'}")
    print(f"🔗 Прямое подключение: {'✅ Успешно' if direct_success else '❌ Ошибка'}")
    
    if docker_success or direct_success:
        print("\n🎉 PostgreSQL доступен!")
        return True
    else:
        print("\n❌ PostgreSQL недоступен!")
        print("\n🔧 Рекомендации:")
        print("  1. Проверьте статус контейнера: docker-compose ps")
        print("  2. Проверьте логи: docker-compose logs postgres")
        print("  3. Перезапустите контейнеры: docker-compose restart")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
