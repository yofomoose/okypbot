#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import numpy as np
import json
import os

def test_migrated_model(model_dir="bot_model"):
    '''
    Простой тест мигрированной модели
    '''
    
    print("🧪 Тестирование мигрированной модели...")
    print("=" * 50)
    
    try:
        # Загружаем компоненты
        classifier_path = os.path.join(model_dir, "classifier.pkl")
        encoder_path = os.path.join(model_dir, "label_encoder.pkl")
        metadata_path = os.path.join(model_dir, "model_metadata.json")
        
        # Проверяем наличие файлов
        required_files = [classifier_path, encoder_path, metadata_path]
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"❌ Не найден файл: {file_path}")
                return False
        
        print("✓ Все необходимые файлы найдены")
        
        # Загружаем модель
        with open(classifier_path, 'rb') as f:
            classifier = pickle.load(f)
        print(f"✓ Модель загружена: {type(classifier).__name__}")
        
        # Загружаем энкодер
        with open(encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print(f"✓ Энкодер загружен, классы: {len(label_encoder.classes_)}")
        
        # Загружаем метаданные
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"✓ Метаданные загружены")
        
        # Выводим информацию о модели
        print("\n📊 Информация о модели:")
        print(f"  Тип: {metadata.get('model_type', 'Неизвестно')}")
        print(f"  Признаков: {metadata.get('feature_count', 'Неизвестно')}")
        print(f"  Обучающих примеров: {metadata.get('training_samples', 'Неизвестно')}")
        print(f"  Количество соседей: {metadata.get('n_neighbors', 'Неизвестно')}")
        print(f"  Классов: {len(metadata.get('classes', []))}")
        
        # Показываем несколько примеров категорий
        classes = metadata.get('classes', [])
        if classes:
            print(f"\n📋 Примеры категорий:")
            for i, cat in enumerate(classes[:5]):
                print(f"  {i+1}. {cat}")
            if len(classes) > 5:
                print(f"  ... и ещё {len(classes) - 5} категорий")
        
        # Тестовое предсказание
        if hasattr(classifier, '_fit_X') and len(classifier._fit_X) > 0:
            print("\n🎯 Выполнение тестового предсказания...")
            
            # Берем несколько примеров из обучающих данных
            test_indices = [0, len(classifier._fit_X)//2, len(classifier._fit_X)-1]
            
            for i, idx in enumerate(test_indices):
                if idx < len(classifier._fit_X):
                    test_features = classifier._fit_X[idx:idx+1]
                    prediction = classifier.predict(test_features)
                    
                    # Декодируем предсказание
                    decoded_prediction = label_encoder.inverse_transform(prediction)
                    
                    # Получаем вероятности если возможно
                    if hasattr(classifier, 'predict_proba'):
                        probabilities = classifier.predict_proba(test_features)[0]
                        confidence = np.max(probabilities)
                        print(f"  Тест {i+1}: {decoded_prediction[0]} (уверенность: {confidence:.3f})")
                    else:
                        print(f"  Тест {i+1}: {decoded_prediction[0]}")
            
            print("✅ Тестовые предсказания выполнены успешно")
        
        else:
            print("⚠️ Не удалось получить обучающие данные для тестирования")
        
        print("\n🎉 Тест завершен успешно!")
        print("✅ Модель готова к использованию")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Простой тест мигрированной модели")
    
    # Запускаем тест
    success = test_migrated_model()
    
    if success:
        print("\n💡 Следующие шаги:")
        print("1. Замените векторизацию в bot_integration_example.py")
        print("2. Установите токен бота")
        print("3. Запустите python bot_integration_example.py")
    else:
        print("\n❌ Тест не пройден. Проверьте миграцию.")
