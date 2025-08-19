"""
ML модуль для классификации заявок
"""

from .classifier import TextClassifier
from .advanced_custom_model import AdvancedCustomModelAdapter

# Совместимость с предыдущим именем
IssueClassifier = TextClassifier

__all__ = ['TextClassifier', 'IssueClassifier', 'AdvancedCustomModelAdapter']
