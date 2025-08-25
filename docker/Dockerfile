# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim AS base

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
FROM base AS deps

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
FROM deps AS development

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
FROM base AS production

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

# Копируем код приложения
COPY --chown=app:app . /app/

# Переключаемся на пользователя app
USER app
WORKDIR /app

# Запускаем бот
CMD ["python", "main.py"]
