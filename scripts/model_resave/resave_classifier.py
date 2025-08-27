import joblib
import os

files = [
    ('bot_model/classifier.pkl', 'bot_model/classifier.pkl'),
    ('bot_model/label_encoder.pkl', 'bot_model/label_encoder.pkl'),
    # Добавьте другие файлы, если нужно
]

for src, dst in files:
    if not os.path.exists(src):
        print(f'Файл не найден: {src}')
        continue
    print(f'Загрузка: {src}')
    obj = joblib.load(src)
    print(f'Сохраняем: {dst}')
    joblib.dump(obj, dst)
    print(f'OK: {dst}')