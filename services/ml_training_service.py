"""
Сервис обучения ML модели на основе обратной связи
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MLTrainingService:
    """Сервис обучения модели на основе обратной связи"""
    
    def __init__(self):
        self.training_queue = asyncio.Queue()
        self.is_training = False
        
    async def train_on_feedback(self, classification_id: int, is_correct: bool):
        """Обучает модель на основе обратной связи"""
        try:
            # Получаем данные классификации
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            classification_data = await ml_stats.get_classification(classification_id)
            if not classification_data:
                logger.error(f"Классификация {classification_id} не найдена")
                return
            
            if is_correct:
                # Положительная обратная связь - укрепляем связь
                await self._reinforce_prediction(classification_data)
                logger.info(f"Укреплена правильная классификация {classification_id}")
            else:
                logger.info(f"Отмечена неправильная классификация {classification_id}")
                
        except Exception as e:
            logger.error(f"Ошибка обучения на обратной связи: {e}")
    
    async def train_on_correction(self, classification_id: int, correct_category: str):
        """Обучает модель на исправленной классификации"""
        try:
            # Получаем данные классификации
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            classification_data = await ml_stats.get_classification(classification_id)
            if not classification_data:
                logger.error(f"Классификация {classification_id} не найдена")
                return
            
            # Добавляем пример для обучения
            await self.add_training_example(
                text=classification_data['text'],
                category=correct_category,
                user_id=classification_data.get('user_id'),
                metadata={
                    'classification_id': classification_id,
                    'old_category': classification_data.get('predicted_category'),
                    'correction_type': 'admin_feedback'
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка обучения на исправлении: {e}")
    
    async def add_training_example(self, text: str, category: str, user_id: int = None, metadata: Dict[str, Any] = None):
        """Добавляет пример для обучения модели"""
        try:
            # Сохраняем пример в БД
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            await ml_stats.save_training_example(
                text=text,
                category=category,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Добавляем пример в модель
            from services.ml_service import ml_service
            
            if ml_service and ml_service.classifier:
                # Добавляем пример для KNN (асинхронно)
                await ml_service.classifier.add_training_example(text, category)
                
                # Увеличиваем счетчик исправлений
                ml_service.classifier._user_corrections += 1
                
                # Отключаем LightGBM после достижения порога исправлений
                if (ml_service.classifier._user_corrections >= 
                    ml_service.classifier._correction_threshold and 
                    hasattr(ml_service.classifier, 'use_lightgbm') and
                    ml_service.classifier.use_lightgbm):
                    
                    ml_service.classifier.use_lightgbm = False
                    logger.info(f"LightGBM отключен после {ml_service.classifier._user_corrections} исправлений")
                
                # Очищаем кеш для пересчета предсказаний
                ml_service.classifier.clear_cache()
                
                logger.info(f"Добавлен обучающий пример: '{text[:50]}...' -> '{category}'")
            
        except Exception as e:
            logger.error(f"Ошибка добавления обучающего примера: {e}")

    async def _reinforce_prediction(self, classification_data: Dict[str, Any]):
        """Укрепляет правильное предсказание"""
        try:
            # Сохраняем положительный пример в базу данных
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            await ml_stats.save_training_example(
                text=classification_data.get('text', ''),
                category=classification_data.get('predicted_category', ''),
                user_id=classification_data.get('user_id', 0),
                example_type='positive_feedback',
                metadata={
                    'confidence': classification_data.get('confidence', 0.0),
                    'classification_id': classification_data.get('id')
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка укрепления предсказания: {e}")
    
    async def _add_training_example(self, text: str, correct_category: str, 
                                  wrong_category: str, classification_id: int):
        """Добавляет исправленный пример в обучающие данные"""
        try:
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            # Сохраняем исправленный пример
            await ml_stats.save_training_example(
                text=text,
                category=correct_category,
                user_id=0,  # Системный пользователь для исправлений
                example_type='correction',
                metadata={
                    'wrong_category': wrong_category,
                    'corrected_at': datetime.now().isoformat(),
                    'classification_id': classification_id
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка добавления обучающего примера: {e}")
    
    async def _check_retrain_needed(self):
        """Проверяет нужно ли переобучить модель"""
        try:
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            # Получаем количество новых примеров с последнего обучения
            new_examples_count = await ml_stats.get_new_training_examples_count()
            
            # Переобучаем модель если накопилось больше 10 новых примеров
            if new_examples_count >= 10:
                logger.info(f"Запускаем переобучение модели: {new_examples_count} новых примеров")
                await self._retrain_model()
            else:
                logger.info(f"Переобучение не требуется: {new_examples_count} новых примеров")
                
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости переобучения: {e}")
    
    async def _retrain_model(self):
        """Переобучает модель на новых данных"""
        if self.is_training:
            logger.info("Модель уже обучается, пропускаем")
            return
            
        try:
            self.is_training = True
            logger.info("Начинаем переобучение модели...")
            
            # Получаем все обучающие данные
            from services.ml_stats_service import MLStatsService
            ml_stats = MLStatsService()
            
            training_data = await ml_stats.get_all_training_examples()
            
            if len(training_data) < 5:
                logger.warning("Недостаточно данных для переобучения")
                return
            
            # Запускаем обучение модели
            from ml.trainer import ModelTrainer
            trainer = ModelTrainer()
            
            success = await trainer.retrain_on_feedback(training_data)
            
            if success:
                logger.info("Модель успешно переобучена")
                await ml_stats.mark_training_examples_as_used()
            else:
                logger.error("Ошибка переобучения модели")
                
        except Exception as e:
            logger.error(f"Ошибка переобучения модели: {e}")
        finally:
            self.is_training = False

# Глобальный экземпляр сервиса
_training_service: Optional[MLTrainingService] = None

def get_training_service() -> Optional[MLTrainingService]:
    """Получить экземпляр сервиса обучения"""
    return _training_service

def set_training_service(service: MLTrainingService):
    """Установить экземпляр сервиса обучения"""
    global _training_service
    _training_service = service
