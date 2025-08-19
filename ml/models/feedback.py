from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from config.db_config import Base

class UserFeedback(Base):
    """Обратная связь пользователей по классификации"""
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True)
    classification_id = Column(Integer, ForeignKey('classifications.id'), nullable=False)
    user_id = Column(BigInteger, nullable=False)  # Изменено на BigInteger
    telegram_user_id = Column(BigInteger, nullable=False)  # Изменено на BigInteger
    
    # Тип обратной связи
    feedback_type = Column(String, nullable=False)  # 'correct', 'incorrect', 'suggestion'
    
    # Детали обратной связи
    is_prediction_correct = Column(Boolean, nullable=True)
    suggested_category = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)  # Обработана ли обратная связь
    processed_at = Column(DateTime, nullable=True)
    
    # Связь с классификацией
    classification = relationship("Classification", backref="feedback")
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type={self.feedback_type}, processed={self.processed})>"
