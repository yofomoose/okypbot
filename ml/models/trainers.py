from sqlalchemy import Column, BigInteger, DateTime, Boolean
from datetime import datetime
from .base import Base

class Trainer(Base):
    __tablename__ = 'trainers'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    added_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Trainer(telegram_id={self.telegram_id})>"
