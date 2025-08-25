# Базовый образ
FROM python:3.11-slim AS bas 
# Удаляем старые установки и кэш
RUN pip uninstall -y numpy scikit-learn scipy || true
RUN pip cache purge || true

# Устанавливаем build-essential для компиляции
RUN apt-get update && apt-get install -y build-essential

# Устанавливаем numpy с полными зависимостями
RUN pip install --no-cache-dir --verbose numpy==1.26.3 && \
    pip install --no-cache-dir --verbose numpy==1.26.3 && \
    python -c "import numpy; print(f'NumPy version: {numpy.__version__}')" && \
    python -m pip install --force-reinstall --no-binary :all: numpy==1.26.3

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir \
    "scikit-learn==1.7.1" \
    "scipy>=1.11.0" \
    "cython>=0.29.0"

# Проверяем установку
RUN python -c "import numpy; from numpy.core import *; print('NumPy core modules:', dir())" && \
    python -c "import numpy, sklearn; print(f'NumPy: {numpy.__version__}, scikit-learn: {sklearn.__version__}')"овка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PATH="/opt/venv/bin:$PATH"

# Создаем пользователя
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash app

# Установка зависимостей
FROM base AS builder

WORKDIR /build

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    python3-dev \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем базовые инструменты
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем и устанавливаем requirements.txt
COPY requirements.txt .

# Очищаем кэш pip и удаляем старые установки
RUN pip uninstall -y numpy scikit-learn scipy; pip cache purge

# Устанавливаем точные версии, которые использовались при сохранении модели
RUN pip install --no-cache-dir "numpy==1.26.3" && \
    python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

# Устанавливаем scikit-learn той же версии, что использовалась при сохранении
RUN pip install --no-cache-dir \
    "scikit-learn==1.7.1" \
    "scipy>=1.11.0"

# Проверяем установленные версии
RUN python -c "import numpy, sklearn; print(f'NumPy: {numpy.__version__}, scikit-learn: {sklearn.__version__}')" && \
    python -c "import numpy._core; print('numpy._core successfully imported')"

# Устанавливаем PyTorch CPU версию
RUN pip install --no-cache-dir torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Проверяем установку numpy
RUN python -c "import numpy; print(f'numpy version: {numpy.__version__}')"

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM base AS production

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Установка минимальных системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем все нужные директории за один RUN
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/ml/models/backups \
    /app/ml/models/cache \
    /app/ml/trained \
    /app/models/backups \
    /app/bot_model \
    /app/temp \
    /app/cache \
    && chown -R app:app /app \
    && chmod -R 755 /app

WORKDIR /app

# Копируем код приложения
COPY --chown=app:app . .

# Проверяем наличие файлов модели и их права доступа
RUN ls -la /app/bot_model/ || true && \
    chown -R app:app /app/bot_model && \
    chmod -R 755 /app/bot_model

# Добавляем отладочный скрипт
COPY --chown=app:app <<EOF /app/debug_model.py
import pickle
import numpy as np
import sys
import os

def debug_model():
    try:
        print(f"Python version: {sys.version}")
        print(f"NumPy version: {np.__version__}")
        
        model_path = "/app/bot_model/classifier.pkl"
        print(f"\nПроверка файла модели:")
        print(f"Существует: {os.path.exists(model_path)}")
        if os.path.exists(model_path):
            print(f"Размер: {os.path.getsize(model_path)} байт")
            print(f"Права доступа: {oct(os.stat(model_path).st_mode)[-3:]}")
            
            print("\nЗагрузка модели...")
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print(f"Тип модели: {type(model)}")
            print(f"Атрибуты модели: {dir(model)}")
            
    except Exception as e:
        print(f"Ошибка при отладке: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_model()
EOF

# Запускаем отладку при старте контейнера
RUN python /app/debug_model.py || true

USER app

CMD ["python", "main.py"]