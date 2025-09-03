# Базовый образ
FROM python:3.11-slim AS base

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PATH="/opt/venv/bin:$PATH"

# Создаем пользователя с правильными UID/GID
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash app

# Создаем рабочие директории с правильными правами
RUN mkdir -p /app/bot_model /app/logs /app/data /tmp/okypbot_models && \
    chown -R app:app /app /tmp/okypbot_models

# Установка зависимостей
FROM base AS builder

# Устанавливаем переменные окружения для NumPy
ENV OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    NUMPY_EXPERIMENTAL_ARRAY_FUNCTION=0

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
    gfortran \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    liblapack3 \
    libssl-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем базовые инструменты
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем requirements.txt и устанавливаем numpy отдельно
COPY requirements.txt .

# Настройка переменных окружения для сборки numpy
ENV NPY_NUM_BUILD_JOBS=4 \
    NUMPY_EXPERIMENTAL_ARRAY_FUNCTION=0 \
    OPENBLAS_NUM_THREADS=1

# Устанавливаем numpy отдельно с совместимой версией
RUN pip install --no-cache-dir numpy==1.24.3 --no-binary numpy && \
    python -c "import numpy; print('NumPy установлен успешно:', numpy.__version__)"

# Устанавливаем ML зависимости (исключая numpy, так как уже установлен)
RUN pip install --no-cache-dir \
    "scikit-learn==1.4.0" \
    "scipy==1.11.2" \
    "pandas==2.0.3" \
    "joblib==1.3.2" && \
    python -c "import numpy, scipy, sklearn, pandas; print('ML dependencies installed successfully')"

# Устанавливаем PyTorch CPU версию
RUN pip install --no-cache-dir torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Создаем временный файл с отфильтрованными зависимостями (исключая ML библиотеки и комментарии)
RUN grep -v -E "^#|^$|numpy|scikit-learn|scipy|pandas|joblib|torch" requirements.txt > /tmp/filtered_requirements.txt && \
    pip install --no-cache-dir -r /tmp/filtered_requirements.txt

# Финальный образ
FROM base AS production

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv


# Установка минимальных системных зависимостей для numpy/scipy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas0 \
    libblas3 \
    liblapack3 \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем все нужные директории с расширенными правами
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
    /tmp/okypbot_examples \
    && chown -R app:app /app /tmp/okypbot_examples \
    && chmod -R 755 /app \
    && chmod -R 777 /app/bot_model /app/logs /app/data /tmp/okypbot_examples

WORKDIR /app

# Копируем код приложения
COPY --chown=app:app . .

# Проверяем наличие файлов модели и устанавливаем правильные права
RUN ls -la /app/bot_model/ || true && \
    chown -R app:app /app/bot_model && \
    chmod -R 777 /app/bot_model && \
    # Создаем файл training_examples.pkl с правильными правами если его нет
    if [ ! -f /app/bot_model/training_examples.pkl ]; then \
        echo "Creating empty training examples file" && \
        touch /app/bot_model/training_examples.pkl && \
        chown app:app /app/bot_model/training_examples.pkl && \
        chmod 666 /app/bot_model/training_examples.pkl; \
    fi && \
    # Исправляем права на все важные директории после копирования
    chown -R app:app /app/data /app/logs /app/temp /app/cache /tmp/okypbot_examples && \
    chmod -R 777 /app/bot_model /app/logs /app/data /app/temp /app/cache /tmp/okypbot_examples


# Проверка наличия numpy в venv
RUN /opt/venv/bin/pip show numpy

USER app


# Проверяем корректность установки numpy и его core-модуля
RUN /opt/venv/bin/python -c "import numpy; print('NumPy version:', numpy.__version__); import numpy.core; print('NumPy core import OK')"
RUN python -c "import numpy; from numpy.core import *; print('NumPy core loaded successfully')"

# Проверяем установку ML зависимостей
RUN /opt/venv/bin/python -c "import sklearn, torch, transformers, sentence_transformers; print('ML dependencies OK')"

# Добавляем скрипт проверки базы данных
COPY --chown=app:app scripts/check_database.sh /app/scripts/
RUN chmod +x /app/scripts/check_database.sh

# Команда запуска приложения
CMD ["/bin/bash", "-c", "/app/scripts/check_database.sh && python main.py"]
