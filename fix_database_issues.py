#!/usr/bin/env python3
"""
Скрипт для диагностики и исправления проблем с базой данных
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from config.db_config import get_session, engine, Base
from ml.models.tables import Classification, User
from ml.models.stats import UsageStats, ModelStats
from ml.models.feedback import UserFeedback
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Проверяет подключение к базе данных"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def check_tables_exist():
    """Проверяет существование необходимых таблиц"""
    inspector = inspect(engine)
    required_tables = ['classifications', 'users', 'usage_stats', 'model_stats', 'user_feedback']

    existing_tables = inspector.get_table_names()
    logger.info(f"Существующие таблицы: {existing_tables}")

    missing_tables = []
    for table in required_tables:
        if table not in existing_tables:
            missing_tables.append(table)

    if missing_tables:
        logger.warning(f"❌ Отсутствуют таблицы: {missing_tables}")
        return False
    else:
        logger.info("✅ Все необходимые таблицы существуют")
        return True

def check_table_structure():
    """Проверяет структуру таблиц"""
    inspector = inspect(engine)

    # Проверяем таблицу classifications
    columns = inspector.get_columns('classifications')
    column_names = [col['name'] for col in columns]

    required_columns = ['id', 'text', 'predicted_category', 'confidence', 'user_id', 'telegram_user_id', 'created_at']

    missing_columns = []
    for col in required_columns:
        if col not in column_names:
            missing_columns.append(col)

    if missing_columns:
        logger.warning(f"❌ В таблице classifications отсутствуют столбцы: {missing_columns}")
        return False
    else:
        logger.info("✅ Структура таблицы classifications корректна")

    return True

def fix_classification_table():
    """Исправляет структуру таблицы classifications"""
    try:
        with engine.connect() as conn:
            # Проверяем и добавляем отсутствующие столбцы
            inspector = inspect(engine)
            columns = inspector.get_columns('classifications')
            column_names = [col['name'] for col in columns]

            # Добавляем user_id если отсутствует
            if 'user_id' not in column_names:
                logger.info("Добавляем столбец user_id в таблицу classifications")
                conn.execute(text("ALTER TABLE classifications ADD COLUMN user_id INTEGER"))
                conn.commit()

            # Добавляем telegram_user_id если отсутствует
            if 'telegram_user_id' not in column_names:
                logger.info("Добавляем столбец telegram_user_id в таблицу classifications")
                conn.execute(text("ALTER TABLE classifications ADD COLUMN telegram_user_id INTEGER"))
                conn.commit()

            # Переименовываем category в predicted_category если нужно
            if 'category' in column_names and 'predicted_category' not in column_names:
                logger.info("Переименовываем столбец category в predicted_category")
                conn.execute(text("ALTER TABLE classifications RENAME COLUMN category TO predicted_category"))
                conn.commit()

            logger.info("✅ Структура таблицы classifications исправлена")
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка исправления таблицы classifications: {e}")
        return False

def create_missing_tables():
    """Создает отсутствующие таблицы"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Все таблицы созданы/обновлены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        return False

def test_database_operations():
    """Тестирует основные операции с базой данных"""
    try:
        with get_session() as session:
            # Тестируем создание пользователя
            test_user = User(
                telegram_id=123456789,
                is_admin=False,
                is_trainer=False
            )
            session.add(test_user)
            session.commit()
            logger.info(f"✅ Создан тестовый пользователь с ID: {test_user.id}")

            # Тестируем создание классификации
            test_classification = Classification(
                text="Тестовый текст",
                predicted_category="Тестовая категория",
                confidence=0.95,
                user_id=test_user.id,
                telegram_user_id=123456789
            )
            session.add(test_classification)
            session.commit()
            logger.info(f"✅ Создана тестовая классификация с ID: {test_classification.id}")

            # Тестируем получение данных
            classification_data = session.query(Classification).filter_by(id=test_classification.id).first()
            if classification_data:
                logger.info(f"✅ Получена классификация: {classification_data.predicted_category}")

            # Очищаем тестовые данные
            session.delete(test_classification)
            session.delete(test_user)
            session.commit()
            logger.info("✅ Тестовые данные удалены")

            return True

    except Exception as e:
        logger.error(f"❌ Ошибка тестирования операций с БД: {e}")
        return False

def main():
    """Основная функция диагностики"""
    logger.info("🔍 Начинаем диагностику базы данных...")

    # 1. Проверяем подключение
    if not check_database_connection():
        logger.error("❌ Невозможно продолжить без подключения к БД")
        return False

    # 2. Проверяем существование таблиц
    if not check_tables_exist():
        logger.info("📝 Создаем отсутствующие таблицы...")
        if not create_missing_tables():
            return False

    # 3. Проверяем структуру таблиц
    if not check_table_structure():
        logger.info("🔧 Исправляем структуру таблиц...")
        if not fix_classification_table():
            return False

    # 4. Тестируем операции
    logger.info("🧪 Тестируем операции с базой данных...")
    if not test_database_operations():
        return False

    logger.info("✅ Диагностика завершена успешно!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
