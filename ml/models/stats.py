from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, BigInteger
from datetime import datetime
from config.db_config import Base

class UsageStats(Base):
    """Статистика использования ML сервиса"""
    __tablename__ = 'usage_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)  # Изменено на BigInteger
    telegram_user_id = Column(BigInteger, nullable=False)  # Изменено на BigInteger
    action_type = Column(String, nullable=False)  # classify, feedback, training
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time = Column(Float, nullable=True)  # Время обработки
    success = Column(Boolean, default=True)  # Успешно ли выполнено

    def __repr__(self):
        return f"<UsageStats(id={self.id}, user_id={self.user_id}, action={self.action_type})>"

class ModelStats(Base):
    """Статистика моделей ML"""
    __tablename__ = 'model_stats'
    
    id = Column(Integer, primary_key=True)
    model_version = Column(String, nullable=False)
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, nullable=True)  # Точность модели
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Статистика по категориям
    category_stats = Column(JSON, nullable=True)  # {"category": {"predictions": X, "correct": Y}}
    
    def __repr__(self):
        return f"<ModelStats(id={self.id}, version={self.model_version}, accuracy={self.accuracy})>"
