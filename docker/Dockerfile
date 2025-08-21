FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
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
    && chmod -R 755 /app

# Переключаемся на пользователя app
USER app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем и устанавливаем зависимости
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

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

# Добавляем пользовательские пакеты в PATH
ENV PATH=/home/app/.local/bin:$PATH

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