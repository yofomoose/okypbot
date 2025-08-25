# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as base

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1

# Создаем пользователя app заранее (без sudo для production)
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash app

# =============================================================================
# STAGE: Dependencies installation
# =============================================================================
FROM base as deps

# Устанавливаем системные зависимости в одном слое
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    python3-dev \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем файлы зависимостей
COPY requirements.txt /tmp/requirements.txt

# Устанавливаем Python зависимости в определенном порядке для лучшего кэширования
RUN pip install --no-cache-dir wheel setuptools

# Устанавливаем numpy отдельно (базовая зависимость для многих пакетов)
RUN pip install --no-cache-dir "numpy==1.24.3"

# Устанавливаем научные библиотеки
RUN pip install --no-cache-dir \
    "scipy==1.11.2" \
    "scikit-learn==1.3.0"

# Устанавливаем ML фреймворки
RUN pip install --no-cache-dir \
    "torch==2.0.1" \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    "transformers==4.31.0" \
    "sentence-transformers==2.2.2" \
    "lightgbm==3.3.2"

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =============================================================================  
# STAGE: Development (опционально)
# =============================================================================
FROM deps as development

RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    htop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER app
WORKDIR /app

# =============================================================================
# STAGE: Production
# =============================================================================
FROM base as production

# Копируем установленные пакеты из stage deps
COPY --from=deps /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# Устанавливаем только curl для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
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

# Устанавливаем переменные окружения для оптимизации
ENV PYTHONPATH=/app \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false

# Переключаемся на пользователя app
USER app
WORKDIR /app

# Копируем код приложения (исключаем ненужные файлы через .dockerignore)
COPY --chown=app:app . .

# Проверяем что все зависимости установлены
RUN python -c "import torch, lightgbm, transformers, sentence_transformers; print('All ML dependencies OK')"

# Проверяем права на запись в рабочие директории
RUN touch ml/models/.write_test && rm ml/models/.write_test

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

EXPOSE 8000

# Используем exec форму для правильной обработки сигналов
CMD ["python", "main.py"]