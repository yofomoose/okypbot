from typing import List, Tuple
import numpy as np
from sklearn.preprocessing import LabelEncoder
from config.settings import VALID_CATEGORIES, MIN_TEXT_LENGTH, MAX_TEXT_LENGTH

class MLUtils:
    @staticmethod
    def validate_text(text: str) -> bool:
        if not MIN_TEXT_LENGTH <= len(text) <= MAX_TEXT_LENGTH:
            return False
        return True
        
    @staticmethod
    def validate_category(category: str) -> bool:
        return category in VALID_CATEGORIES
        
    @staticmethod
    def prepare_labels(labels: List[str]) -> Tuple[np.ndarray, LabelEncoder]:
        encoder = LabelEncoder()
        encoded_labels = encoder.fit_transform(labels)
        return encoded_labels, encoder
