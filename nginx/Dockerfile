FROM nginx:alpine

# Создаем директории для логов
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Копируем конфигурационные файлы
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Экспортируем порты
EXPOSE 80 443

# Добавляем healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -q --spider http://localhost/health || exit 1
