from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, BigInteger
from datetime import datetime
from config.db_config import Base

class Classification(Base):
    """Модель для хранения результатов классификации"""
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)  # Упрощено без шифрования
    category = Column(String, nullable=False)
    confidence = Column(Float)
    telegram_user_id = Column(BigInteger)  # Изменено на BigInteger для больших Telegram ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Поля для обратной связи и обучения
    is_correct = Column(Boolean, nullable=True)  # Правильно ли классифицировано (пользователь подтверждает)
    correct_category = Column(String, nullable=True)  # Правильная категория, если is_correct=False
    feedback_at = Column(DateTime, nullable=True)  # Когда получена обратная связь
    is_training = Column(Boolean, default=False)  # Используется ли для обучения
    
    # Техническая информация
    model_version = Column(String, nullable=True)  # Версия модели
    processing_time = Column(Float, nullable=True)  # Время обработки в секундах

    def __repr__(self):
        return f"<Classification(id={self.id}, category={self.category}, confidence={self.confidence})>"
