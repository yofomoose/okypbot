"""
Безопасный загрузчик моделей с поддержкой различных форматов
"""

import numpy as np
import joblib
import pickle
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

def safe_load_model(model_path: str) -> Optional[Any]:
    """
    Безопасная загрузка модели с поддержкой различных форматов
    """
    path = Path(model_path)
    if not path.exists():
        logger.error(f"Файл модели не найден: {model_path}")
        return None
        
    try:
        # Пробуем загрузить через joblib
        logger.info("Пробуем загрузить через joblib...")
        model = joblib.load(model_path)
        logger.info("Модель успешно загружена через joblib")
        return model
    except Exception as e:
        logger.warning(f"Не удалось загрузить через joblib: {e}")
        
    try:
        # Пробуем различные варианты pickle
        with open(model_path, 'rb') as f:
            try:
                logger.info("Пробуем pickle с latin1...")
                model = pickle.load(f, encoding='latin1')
                return model
            except:
                f.seek(0)
                try:
                    logger.info("Пробуем pickle с bytes...")
                    model = pickle.load(f, encoding='bytes')
                    return model
                except:
                    f.seek(0)
                    try:
                        logger.info("Пробуем pickle без encoding...")
                        model = pickle.load(f)
                        return model
                    except Exception as e:
                        logger.error(f"Все методы загрузки завершились неудачей: {e}")
                        return None
    except Exception as e:
        logger.error(f"Критическая ошибка при загрузке модели: {e}")
        return None
