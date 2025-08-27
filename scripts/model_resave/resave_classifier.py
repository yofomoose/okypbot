import joblib
import os

# Путь к исходной модели (относительно корня проекта)
SRC_MODEL_PATH = os.path.join('bot_model', 'classifier.pkl')
DST_MODEL_PATH = os.path.join('bot_model', 'classifier.pkl')

if not os.path.exists(SRC_MODEL_PATH):
    raise FileNotFoundError(f'Исходная модель не найдена: {SRC_MODEL_PATH}')

print(f'Загрузка модели из {SRC_MODEL_PATH}...')
model = joblib.load(SRC_MODEL_PATH)

print(f'Сохраняем модель в {DST_MODEL_PATH}...')
joblib.dump(model, DST_MODEL_PATH)
print('Модель успешно пересохранена!')