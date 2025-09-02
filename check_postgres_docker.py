#!/usr/bin/env python3
"""
Скрипт для проверки подключения к PostgreSQL в Docker
"""

import psycopg2
import os
import sys
from datetime import datetime

def check_postgres_connection():
    """Проверяет подключение к PostgreSQL"""
    
    print("🔍 Проверка подключения к PostgreSQL в Docker")
    print("=" * 50)
    
    # Параметры подключения для Docker
    db_configs = [
        {
            "name": "Docker Internal (postgres:5432)",
            "host": "postgres",
            "port": 5432,
            "database": "okypbot",
            "user": "postgres",
            "password": "Cnhjywsq97"
        },
        {
            "name": "Docker External (localhost:5433)",
            "host": "localhost", 
            "port": 5433,
            "database": "okypbot",
            "user": "postgres",
            "password": "Cnhjywsq97"
        }
    ]
    
    for config in db_configs:
        print(f"\n📋 Тестируем: {config['name']}")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   Database: {config['database']}")
        print(f"   User: {config['user']}")
        
        try:
            # Подключение к базе данных
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            
            # Проверяем версию PostgreSQL
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Подключение успешно!")
            print(f"   Версия: {version.split(',')[0]}")
            
            # Проверяем таблицы
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"   Таблицы ({len(tables)}):")
                for table in tables:
                    print(f"     - {table[0]}")
            else:
                print("   ⚠️  Таблицы не найдены")
            
            # Проверяем статус подключений
            cursor.execute("""
                SELECT count(*) as active_connections 
                FROM pg_stat_activity 
                WHERE state = 'active';
            """)
            active_conn = cursor.fetchone()[0]
            print(f"   Активных подключений: {active_conn}")
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            print(f"❌ Ошибка подключения: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

def check_docker_containers():
    """Проверяет статус Docker контейнеров"""
    print(f"\n🐳 Проверка Docker контейнеров")
    print("=" * 30)
    
    import subprocess
    
    try:
        # Проверяем статус контейнеров
        result = subprocess.run(
            ["docker-compose", "ps"], 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("📊 Статус контейнеров:")
            print(result.stdout)
        else:
            print(f"❌ Ошибка получения статуса: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ Docker Compose не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_env_variables():
    """Проверяет переменные окружения"""
    print(f"\n🔧 Переменные окружения")
    print("=" * 25)
    
    env_vars = [
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
        "BOT_TOKEN", "OKDESK_API_TOKEN", "WEBHOOK_PORT"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "НЕ УСТАНОВЛЕНА")
        if var in ["BOT_TOKEN", "OKDESK_API_TOKEN", "DB_PASSWORD"]:
            # Скрываем чувствительные данные
            if value != "НЕ УСТАНОВЛЕНА":
                value = value[:8] + "..." if len(value) > 8 else "***"
        print(f"   {var}: {value}")

if __name__ == "__main__":
    print(f"🚀 Диагностика PostgreSQL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_env_variables()
    check_docker_containers()
    check_postgres_connection()
    
    print(f"\n✨ Диагностика завершена")
