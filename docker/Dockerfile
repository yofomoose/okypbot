FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя app
RUN useradd --create-home --shell /bin/bash app

# Создаем рабочую директорию и все поддиректории СРАЗУ
RUN mkdir -p /app \
    /app/data \
    /app/logs \
    /app/ml \
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

# Предварительная установка тяжелых ML зависимостей
RUN pip install --no-cache-dir --user \
    numpy \
    scipy \
    scikit-learn \
    pandas \
    torch \
    transformers \
    sentence-transformers \
    lightgbm

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

# Проверка установки ML зависимостей
RUN python -c "import sentence_transformers; import lightgbm; import torch; print('ML dependencies OK')"

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