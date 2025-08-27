import joblib
import os

files = [
    'bot_model/classifier.pkl',
    'bot_model/label_encoder.pkl',
    'ml/models/classifier.pkl',
    'ml/models/label_encoder.pkl',
    'ml/models/examples.pkl',
    'ml/models/training_examples.pkl',
    'ml/models/backups/backup_20250819_173801/classifier.pkl',
    'ml/models/backups/backup_20250819_173801/examples.pkl',
    'ml/models/backups/backup_20250819_190317/classifier.pkl',
    'ml/models/backups/backup_20250819_190317/examples.pkl',
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