FROM nginx:alpine

# Копируем конфигурационные файлы
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Проверяем конфигурацию
RUN nginx -t

# Экспортируем порты
EXPOSE 80 443

# Добавляем healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -q --spider http://localhost/health || exit 1
