FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание ВСЕХ возможных директорий заранее (включая ml/models/backups)
RUN mkdir -p \
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
    && chown -R app:app /app

# Переключение на пользователя app
USER app

# Экспорт портов
EXPOSE 8000

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда по умолчанию
CMD ["python", "main.py"]