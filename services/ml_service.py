"""
Сервис машинного обучения для классификации заявок
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from ml.classifier import TextClassifier

logger = logging.getLogger(__name__)

class MLService:
    """Сервис для работы с ML классификацией заявок"""
    
    def __init__(self):
        self.classifier = TextClassifier()
        self.is_initialized = False
        self.classification_history = []
        self.max_history_size = 1000
    
    async def initialize(self) -> bool:
        """Инициализация ML сервиса"""
        try:
            logger.info("Инициализация ML сервиса...")
            self.is_initialized = await self.classifier.initialize()
            
            if self.is_initialized:
                stats = self.classifier.get_stats()
                logger.info(f"ML сервис инициализирован: {stats}")
            else:
                logger.warning("ML сервис инициализирован в базовом режиме")
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации ML сервиса: {e}")
            return False
    
    async def classify_issue(self, issue_text: str, user_id: int = None) -> Dict:
        """
        Классификация текста заявки с сохранением в БД
        
        Args:
            issue_text: Текст заявки
            user_id: ID пользователя (для статистики)
            
        Returns:
            Dict с результатами классификации и ID записи в БД
        """
        start_time = time.time()
        
        if not issue_text or not issue_text.strip():
            return {
                'category': 'Другое',
                'confidence': 0.0,
                'error': 'Пустой текст заявки'
            }
        
        try:
            # Классифицируем
            category, confidence = await self.classifier.classify(issue_text)
            processing_time = time.time() - start_time
            
            # Определяем рекомендации
            recommendations = self._get_recommendations(category, confidence)
            
            # Сохраняем в историю
            classification_result = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'text': issue_text[:100] + '...' if len(issue_text) > 100 else issue_text,
                'category': category,
                'confidence': confidence,
                'recommendations': recommendations,
                'processing_time': processing_time
            }
            
            self._add_to_history(classification_result)
            
            # Сохраняем в БД (если доступно)
            classification_id = None
            try:
                from services.ml_stats_service import ml_stats_service
                classification_id = ml_stats_service.save_classification(
                    text=issue_text,
                    predicted_category=category,
                    confidence=confidence,
                    user_id=user_id or 0,
                    telegram_user_id=user_id or 0,
                    processing_time=processing_time
                )
            except Exception as db_error:
                logger.warning(f"Не удалось сохранить в БД: {db_error}")
            
            return {
                'category': category,
                'confidence': confidence,
                'recommendations': recommendations,
                'success': True,
                'classification_id': classification_id,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Ошибка классификации: {e}")
            return {
                'category': 'Другое',
                'confidence': 0.0,
                'error': str(e),
                'success': False
            }
    
    def _get_recommendations(self, category: str, confidence: float) -> List[str]:
        """Получение рекомендаций на основе классификации"""
        recommendations = []
        
        # Общие рекомендации по уверенности
        if confidence < 0.3:
            recommendations.append("🔍 Низкая уверенность классификации. Рекомендуется уточнить описание проблемы")
        elif confidence < 0.6:
            recommendations.append("⚠️ Средняя уверенность классификации. Возможно, стоит добавить больше деталей")
        
        # Специфичные рекомендации по категориям
        category_recommendations = {
            "Проблемы с доступом": [
                "🔑 Укажите ваш логин или email",
                "📱 Попробуйте сбросить пароль через форму восстановления",
                "⏰ Укажите, когда проблема началась"
            ],
            "Ошибки в работе системы": [
                "🖥️ Укажите код ошибки, если есть",
                "🌐 Укажите браузер и его версию",
                "📸 Приложите скриншот ошибки, если возможно"
            ],
            "Техническая поддержка": [
                "📋 Опишите, что именно нужно настроить",
                "🎯 Укажите желаемый результат",
                "⚙️ Укажите вашу роль в системе"
            ],
            "Консультация": [
                "❓ Сформулируйте конкретный вопрос",
                "📚 Укажите, с какой функцией нужна помощь",
                "🎯 Опишите, что пытаетесь достичь"
            ],
            "Запрос на изменение": [
                "📝 Опишите текущее состояние",
                "🎯 Опишите желаемое изменение",
                "⚡ Укажите приоритет запроса"
            ]
        }
        
        if category in category_recommendations:
            recommendations.extend(category_recommendations[category])
        
        return recommendations
    
    def _add_to_history(self, result: Dict):
        """Добавление результата в историю"""
        self.classification_history.append(result)
        
        # Ограничиваем размер истории
        if len(self.classification_history) > self.max_history_size:
            self.classification_history = self.classification_history[-self.max_history_size:]
    
    async def add_feedback(self, text: str, correct_category: str, user_id: int = None) -> bool:
        """
        Добавление обратной связи для улучшения модели
        
        Args:
            text: Текст заявки
            correct_category: Правильная категория
            user_id: ID пользователя
            
        Returns:
            bool: Успешность добавления
        """
        try:
            success = await self.classifier.add_training_example(text, correct_category)
            
            if success:
                logger.info(f"Добавлена обратная связь: категория '{correct_category}' от пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка добавления обратной связи: {e}")
            return False
    
    async def retrain_model(self) -> bool:
        """Переобучение модели"""
        try:
            logger.info("Начинается переобучение модели...")
            success = await self.classifier.retrain_model()
            
            if success:
                logger.info("Модель успешно переобучена")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка переобучения модели: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Получить список доступных категорий"""
        return self.classifier.get_categories()
    
    def enable_lightgbm(self) -> bool:
        """Включить LightGBM модель"""
        return self.classifier.enable_lgb_model()
    
    def disable_lightgbm(self) -> bool:
        """Отключить LightGBM модель (использовать KNN)"""
        return self.classifier.disable_lgb_model()
    
    def get_statistics(self) -> Dict:
        """Получить статистику работы ML сервиса"""
        classifier_stats = self.classifier.get_stats()
        
        # Статистика истории
        history_stats = {}
        if self.classification_history:
            categories = [item['category'] for item in self.classification_history]
            category_counts = {}
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            confidences = [item['confidence'] for item in self.classification_history]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            history_stats = {
                'total_classifications': len(self.classification_history),
                'category_distribution': category_counts,
                'average_confidence': round(avg_confidence, 3),
                'recent_activity': self.classification_history[-5:] if self.classification_history else []
            }
        
        return {
            'service_status': 'active' if self.is_initialized else 'inactive',
            'classifier': classifier_stats,
            'history': history_stats,
            'timestamp': datetime.now().isoformat()
        }

# Глобальный экземпляр сервиса
ml_service = MLService()
