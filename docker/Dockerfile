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

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    python3-dev \
    build-essential \
    libgomp1 \
    libopenblas0 \
    libblas3 \
    liblapack3 \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем базовые инструменты
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем requirements.txt и устанавливаем все зависимости
COPY requirements.txt .

# Устанавливаем все зависимости (numpy будет установлен из wheels)
RUN pip install --no-cache-dir -r requirements.txt

# Проверяем установку ключевых пакетов
RUN python -c "import numpy, scipy, sklearn, torch; print('All ML packages installed successfully')"


# Установка минимальных системных зависимостей для numpy/scipy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas0 \
    libblas3 \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Создаем все нужные директории
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

# Проверяем наличие файлов модели
RUN ls -la /app/bot_model/ || true && \
    chown -R app:app /app/bot_model && \
    chmod -R 755 /app/bot_model

USER app

# Проверяем корректность установки пакетов
RUN python -c "import numpy, scipy, sklearn, torch; print('All packages working correctly')"

# Добавляем скрипт проверки базы данных
COPY --chown=app:app scripts/check_database.sh /app/scripts/
RUN chmod +x /app/scripts/check_database.sh

# Команда запуска приложения
CMD ["/bin/bash", "-c", "/app/scripts/check_database.sh && python main.py"]
