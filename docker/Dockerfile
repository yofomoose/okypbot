# Базовый образ
FROM python:3.11-slim AS base

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

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
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости в несколько этапов для лучшего кэширования
RUN pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir "numpy==1.24.3" && \
    pip install --no-cache-dir \
        "scipy==1.11.2" \
        "scikit-learn==1.3.0" && \
    pip install --no-cache-dir \
        "torch==2.0.1" --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        "transformers==4.31.0" \
        "sentence-transformers==2.2.2" \
        "lightgbm==3.3.2" && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM base AS production

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Установка минимальных системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем структуру директорий
RUN mkdir -p /app/data \
             /app/logs \
             /app/ml/models/backups \
             /app/ml/models/cache \
             /app/ml/trained \
             /app/models/backups \
             /app/temp \
             /app/cache \
    && chown -R app:app /app \
    && chmod -R 755 /app

WORKDIR /app

# Создаем структуру директорий
RUN mkdir -p /app/ml \
    /app/bot_model \
    /app/ml/models/backups \
    /app/ml/models/cache \
    /app/logs \
    /app/data \
    && chown -R app:app /app \
    && chmod -R 755 /app

# Копируем код приложения
COPY --chown=app:app . .

# Копируем модель отдельно, чтобы убедиться что все файлы на месте
COPY --chown=app:app bot_model/*.pkl bot_model/*.json /app/bot_model/

USER app

CMD ["python", "main.py"]
