"""
Конфигурация базы данных
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Загружаем переменные окружения из .env файла
load_dotenv()

# Базовый класс для моделей
Base = declarative_base()

# Конфигурация PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "okypbot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# URL базы данных
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"

# Fallback на SQLite для разработки
SQLITE_URL = "sqlite:///./okypbot.db"

def get_database_url():
    """Возвращает URL базы данных"""
    # Проверяем переменную окружения для отключения PostgreSQL
    disable_postgresql = os.getenv('DISABLE_POSTGRESQL', 'false').lower() == 'true'
    
    if disable_postgresql:
        # Используем SQLite только если PostgreSQL явно отключен
        print(f"✅ Используем SQLite базу данных (PostgreSQL отключен)")
        return SQLITE_URL
    else:
        try:
            # По умолчанию пробуем PostgreSQL
            engine = create_engine(DATABASE_URL)
            with engine.connect():
                pass
            print(f"✅ Подключение к PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return DATABASE_URL
        except Exception as e:
            # Fallback на SQLite только при ошибке
            print(f"⚠️ PostgreSQL недоступен ({e}), используем SQLite")
            return SQLITE_URL

# Создание движка
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переподключение каждый час
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {
        "options": "-c timezone=utc"  # Установка часового пояса для PostgreSQL
    }
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_session():
    """Контекстный менеджер для работы с БД"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ База данных инициализирована: {get_database_url()}")

def check_db_connection():
    """Проверка подключения к БД"""
    try:
        with get_session() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False
