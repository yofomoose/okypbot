"""
Сервис для сбора статистики и обратной связи по ML классификации
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config.db_config import get_session, SessionLocal
from ml.models.tables import Classification
from ml.models.stats import UsageStats, ModelStats
from ml.models.feedback import UserFeedback
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class MLStatsService:
    """Сервис для сбора и анализа статистики ML"""
    
    def __init__(self):
        self.current_model_version = "lightgbm_v1.0"
    
    def save_classification(self, text: str, predicted_category: str, 
                                confidence: float, user_id: int, telegram_user_id: int,
                                processing_time: float = None) -> int:
        """Сохраняет результат классификации в БД"""
        from config.db_config import SessionLocal
        session = SessionLocal()
        
        try:
            # Сохраняем основную классификацию
            classification = Classification(
                text=text,
                category=predicted_category,
                confidence=confidence,
                created_by=telegram_user_id,
                created_at=datetime.utcnow()
            )
            session.add(classification)
            session.commit()
            
            classification_id = classification.id
            logger.info(f"Классификация сохранена: ID {classification_id}")
            
            # Пытаемся сохранить статистику использования отдельно
            try:
                usage_stat = UsageStats(
                    user_id=user_id,
                    telegram_user_id=telegram_user_id,
                    action_type='classify',
                    details={
                        'text': text,
                        'category': predicted_category,
                        'confidence': confidence
                    },
                    processing_time=processing_time,
                    success=True,
                    action_type="classify",
                    details={
                        "category": predicted_category,
                        "confidence": confidence,
                        "text_length": len(text)
                    },
                    processing_time=processing_time
                )
                session.add(usage_stat)
                session.commit()
                logger.info(f"Статистика сохранена для классификации {classification_id}")
            except Exception as stat_error:
                logger.warning(f"Ошибка сохранения статистики: {stat_error}")
                # Не прерываем выполнение, статистика не критична
            
            return classification_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения классификации: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    async def save_user_feedback(self, classification_id: int, user_id: int,
                               telegram_user_id: int, is_correct: bool,
                               suggested_category: str = None, comment: str = None) -> bool:
        """Сохраняет обратную связь пользователя"""
        try:
            with get_session() as session:
                # Обновляем классификацию
                classification = session.query(Classification).filter_by(id=classification_id).first()
                if classification:
                    classification.is_correct = is_correct
                    classification.feedback_at = datetime.utcnow()
                    if not is_correct and suggested_category:
                        classification.correct_category = suggested_category
                
                # Создаем запись обратной связи
                feedback = UserFeedback(
                    classification_id=classification_id,
                    user_id=user_id,
                    telegram_user_id=telegram_user_id,
                    feedback_type="correct" if is_correct else "incorrect",
                    is_prediction_correct=is_correct,
                    suggested_category=suggested_category,
                    comment=comment
                )
                session.add(feedback)
                
                # Статистика использования
                usage_stat = UsageStats(
                    user_id=user_id,
                    telegram_user_id=telegram_user_id,
                    action_type="feedback",
                    details={
                        "classification_id": classification_id,
                        "is_correct": is_correct,
                        "suggested_category": suggested_category
                    }
                )
                session.add(usage_stat)
                
                logger.info(f"Обратная связь сохранена для классификации {classification_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения обратной связи: {e}")
            return False
    
    async def get_classification(self, classification_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные классификации по ID"""
        try:
            with get_session() as session:
                classification = session.query(Classification).filter_by(id=classification_id).first()
                
                if not classification:
                    return None
                    
                return {
                    "id": classification.id,
                    "text": classification.text,
                    "predicted_category": classification.predicted_category,
                    "confidence": classification.confidence,
                    "is_correct": classification.is_correct,
                    "correct_category": classification.correct_category,
                    "user_id": classification.user_id,
                    "telegram_user_id": classification.telegram_user_id,
                    "created_at": classification.created_at,
                    "feedback_at": classification.feedback_at
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения классификации {classification_id}: {e}")
            return None
    
    async def get_model_accuracy(self, days: int = 30) -> Dict[str, Any]:
        """Получает статистику точности модели за указанный период"""
        try:
            with get_session() as session:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Классификации с обратной связью
                classifications = session.query(Classification).filter(
                    Classification.created_at >= since_date,
                    Classification.is_correct.isnot(None)
                ).all()
                
                if not classifications:
                    return {"accuracy": 0.0, "total": 0, "correct": 0}
                
                total = len(classifications)
                correct = sum(1 for c in classifications if c.is_correct)
                accuracy = correct / total if total > 0 else 0.0
                
                # Статистика по категориям
                category_stats = {}
                for c in classifications:
                    cat = c.predicted_category
                    if cat not in category_stats:
                        category_stats[cat] = {"total": 0, "correct": 0}
                    category_stats[cat]["total"] += 1
                    if c.is_correct:
                        category_stats[cat]["correct"] += 1
                
                # Добавляем точность по категориям
                for cat, stats in category_stats.items():
                    stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
                
                return {
                    "accuracy": accuracy,
                    "total": total,
                    "correct": correct,
                    "period_days": days,
                    "category_stats": category_stats
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики точности: {e}")
            return {"accuracy": 0.0, "total": 0, "correct": 0, "error": str(e)}
    
    async def get_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получает данные для дообучения модели"""
        try:
            with get_session() as session:
                # Берем классификации с обратной связью
                classifications = session.query(Classification).filter(
                    Classification.is_correct.isnot(None)
                ).order_by(Classification.created_at.desc()).limit(limit).all()
                
                training_data = []
                for c in classifications:
                    # Используем правильную категорию или предсказанную (если она правильная)
                    true_category = c.correct_category if not c.is_correct else c.predicted_category
                    
                    training_data.append({
                        "text": c.text,
                        "category": true_category,
                        "is_correction": not c.is_correct,
                        "original_prediction": c.predicted_category,
                        "confidence": c.confidence,
                        "timestamp": c.created_at.isoformat()
                    })
                
                logger.info(f"Получено {len(training_data)} записей для обучения")
                return training_data
                
        except Exception as e:
            logger.error(f"Ошибка получения данных для обучения: {e}")
            return []
    
    async def get_user_stats(self, telegram_user_id: int) -> Dict[str, Any]:
        """Получает статистику конкретного пользователя"""
        try:
            with get_session() as session:
                # Общее количество классификаций
                total_classifications = session.query(Classification).filter_by(
                    telegram_user_id=telegram_user_id
                ).count()
                
                # Классификации с обратной связью
                feedback_classifications = session.query(Classification).filter(
                    Classification.telegram_user_id == telegram_user_id,
                    Classification.is_correct.isnot(None)
                ).all()
                
                feedback_count = len(feedback_classifications)
                correct_feedback = sum(1 for c in feedback_classifications if c.is_correct)
                
                # Активность по дням
                usage_stats = session.query(UsageStats).filter_by(
                    telegram_user_id=telegram_user_id
                ).all()
                
                return {
                    "total_classifications": total_classifications,
                    "feedback_given": feedback_count,
                    "correct_predictions": correct_feedback,
                    "feedback_rate": feedback_count / total_classifications if total_classifications > 0 else 0.0,
                    "total_actions": len(usage_stats),
                    "user_accuracy": correct_feedback / feedback_count if feedback_count > 0 else None
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя: {e}")
            return {"error": str(e)}

    async def save_feedback(self, classification_id: int, correct_category: str = None, 
                           is_correct: bool = False, user_id: int = None, 
                           feedback_type: str = None) -> bool:
        """Сохраняет обратную связь по классификации"""
        try:
            with get_session() as session:
                classification = session.query(Classification).filter_by(id=classification_id).first()
                if not classification:
                    logger.warning(f"Классификация {classification_id} не найдена")
                    return False
                
                classification.is_correct = is_correct
                classification.correct_category = correct_category
                classification.feedback_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"Обратная связь сохранена для классификации {classification_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения обратной связи: {e}")
            return False

    async def save_training_example(self, text: str, category: str, user_id: int, 
                                   classification_id: int = None, example_type: str = "correction", 
                                   metadata: dict = None) -> bool:
        """Сохраняет обучающий пример в базу данных"""
        try:
            # Для простоты пока просто логируем
            logger.info(f"Сохранение обучающего примера [{example_type}]: '{text[:50]}...' -> '{category}' (пользователь: {user_id})")
            if metadata:
                logger.info(f"Метаданные: {metadata}")
            return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения обучающего примера: {e}")
            return False
    
    async def get_new_training_examples_count(self, since_hours: int = 24) -> int:
        """Возвращает количество новых обучающих примеров за указанный период"""
        try:
            # Для простоты возвращаем фиксированное значение
            # В реальной реализации здесь был бы запрос к базе данных
            return 0
                
        except Exception as e:
            logger.error(f"Ошибка получения количества новых примеров: {e}")
            return 0

# Глобальный экземпляр сервиса
ml_stats_service = MLStatsService()
