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

# Устанавливаем numpy отдельно первым
RUN pip install --no-cache-dir "numpy==1.24.3"

# Устанавливаем scipy и scikit-learn
RUN pip install --no-cache-dir \
    "scipy==1.11.2" \
    "scikit-learn==1.3.0"

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

USER app

CMD ["python", "main.py"]