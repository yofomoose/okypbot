"""
Скрипт для конвертации модели из pickle в joblib формат
"""

import pickle
import joblib
import numpy as np
from pathlib import Path

def convert_model():
    base_path = Path('bot_model')
    
    # Загружаем classifier.pkl
    print("Загрузка classifier.pkl...")
    with open(base_path / 'classifier.pkl', 'rb') as f:
        classifier = pickle.load(f, encoding='latin1')
    
    # Сохраняем в формате joblib с оптимизацией памяти
    print("Сохранение classifier.joblib...")
    joblib.dump(classifier, base_path / 'classifier.joblib', compress=3)
    
    # Загружаем label_encoder.pkl
    print("Загрузка label_encoder.pkl...")
    with open(base_path / 'label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f, encoding='latin1')
    
    # Сохраняем в формате joblib
    print("Сохранение label_encoder.joblib...")
    joblib.dump(label_encoder, base_path / 'label_encoder.joblib', compress=3)
    
    print("Конвертация завершена!")

if __name__ == '__main__':
    convert_model()
