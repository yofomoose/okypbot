import joblib
import os

files = [
    'bot_model/classifier.pkl',
    'bot_model/label_encoder.pkl',
    # Добавьте другие файлы, если нужно
]

for path in files:
    if not os.path.exists(path):
        print(f'Файл не найден: {path}')
        continue
    print(f'Загрузка: {path}')
    obj = joblib.load(path)
    print(f'Сохраняем: {path}')
    joblib.dump(obj, path)
    print(f'OK: {path}')