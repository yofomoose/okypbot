import joblib
import pickle
import os
import sys

files = [
    'bot_model/classifier.pkl',
    'bot_model/label_encoder.pkl',
    
]

def try_load(path):
    try:
        print(f'Trying joblib.load: {path}')
        obj = joblib.load(path)
        print('  Success: joblib')
        return obj
    except Exception as e_joblib:
        print(f'  joblib.load failed: {e_joblib}')
        try:
            print(f'Trying pickle.load: {path}')
            with open(path, 'rb') as f:
                obj = pickle.load(f)
            print('  Success: pickle')
            return obj
        except Exception as e_pickle:
            print(f'  pickle.load failed: {e_pickle}')
            return None

def main():
    for path in files:
        if not os.path.exists(path):
            print(f'Файл не найден: {path}')
            continue
        print(f'Обработка: {path}')
        obj = try_load(path)
        if obj is None:
            print(f'❌ Не удалось загрузить: {path}')
            continue
        # Сохраняем только через joblib
        try:
            joblib.dump(obj, path)
            print(f'✅ Пересохранено через joblib: {path}')
        except Exception as e:
            print(f'❌ Ошибка при сохранении через joblib: {e}')

if __name__ == '__main__':
    main()
