"""
ML модуль для классификации заявок
"""

from .classifier import TextClassifier
from .advanced_custom_model import AdvancedCustomModelAdapter

# Новые компоненты для bot_model
try:
    from .bot_model_adapter import BotModelAdapter
    from .text_vectorizer import TextVectorizer, text_vectorizer
    BOT_MODEL_AVAILABLE = True
except ImportError:
    BOT_MODEL_AVAILABLE = False

# Совместимость с предыдущим именем
IssueClassifier = TextClassifier

__all__ = ['TextClassifier', 'IssueClassifier', 'AdvancedCustomModelAdapter']

if BOT_MODEL_AVAILABLE:
    __all__.extend(['BotModelAdapter', 'TextVectorizer', 'text_vectorizer'])
