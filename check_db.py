#!/usr/bin/env python3
"""
Проверка создания таблиц в базе данных
"""

# Импортируем модели
from ml.models.tables import User, Classification, TrainingExample
from ml.models.stats import UsageStats, ModelStats  
from ml.models.feedback import UserFeedback

# Инициализируем БД
from config.db_config import init_database
init_database()

# Проверяем таблицы
from config.db_config import get_session
from sqlalchemy import text

with get_session() as session:
    result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result]
    print('Tables in database:', tables)
