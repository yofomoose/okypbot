FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Создаем пользователя app
RUN useradd --create-home --shell /bin/bash app

# Создаем рабочую директорию и все поддиректории СРАЗУ
RUN mkdir -p /app \
    /app/data \
    /app/logs \
    /app/ml \
    /app/database

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH=/app

# Создаем дополнительные директории и устанавливаем права
RUN mkdir -p \
    /app/ml/models \
    /app/ml/models/backups \
    /app/ml/models/cache \
    /app/ml/trained \
    /app/models \
    /app/models/backups \
    /app/temp \
    /app/cache \
    && chown -R app:app /app \
    && chmod -R 777 /app \
    && chmod -R 777 /app/ml/models \
    && chmod -R 777 /app/ml/models/backups \
    && chmod -R 777 /app/ml/models/cache \
    && chmod -R 777 /app/logs

# Создаем директории для ML моделей и даем права на запись
VOLUME ["/app/ml/models", "/app/ml/models/backups", "/app/ml/models/cache"]

# Устанавливаем базовые ML зависимости отдельно
RUN pip install --no-cache-dir numpy>=1.25.0

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменные окружения для NumPy/SciPy
ENV OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1

# Переключаемся на пользователя app
USER app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем и устанавливаем зависимости
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Предварительная установка базовых зависимостей
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user \
    wheel \
    setuptools \
    numpy==1.24.3 \
    scipy==1.11.2

# Установка ML зависимостей по очереди для лучшей кэшируемости
RUN pip install --no-cache-dir --user torch==2.0.1
RUN pip install --no-cache-dir --user transformers==4.31.0
RUN pip install --no-cache-dir --user sentence-transformers==2.2.2
RUN pip install --no-cache-dir --user scikit-learn==1.3.0
RUN pip install --no-cache-dir --user lightgbm==3.3.2

# Копируем код приложения
COPY --chown=app:app . .

# Дополнительная проверка и создание директорий от имени app
RUN mkdir -p \
    data \
    logs \
    ml/models/backups \
    ml/models/cache \
    ml/trained \
    models/backups \
    temp \
    cache \
    || echo "Некоторые директории уже существуют"

# Проверяем права на директории ML
RUN touch ml/models/.write_test && \
    rm ml/models/.write_test && \
    touch ml/models/backups/.write_test && \
    rm ml/models/backups/.write_test && \
    touch ml/models/cache/.write_test && \
    rm ml/models/cache/.write_test || \
    echo "Проверка прав завершена"

# Добавляем пользовательские пакеты в PATH
ENV PATH=/home/app/.local/bin:$PATH

# Проверка базовых ML зависимостей
RUN python -c "import torch; import lightgbm; print('Basic ML dependencies OK')"

# Проверка прав на запись
RUN mkdir -p ml/models ml/models/backups ml/models/cache && \
    touch ml/models/.write_test && \
    rm ml/models/.write_test && \
    echo "Write permissions OK"

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Экспорт портов
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда по умолчанию
CMD ["python", "main.py"]