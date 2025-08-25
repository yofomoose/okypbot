FROM nginx:alpine

# Копируем конфигурационные файлы
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/okypbot_locations.conf /etc/nginx/conf.d/okypbot_locations.conf

# Экспортируем порты
EXPOSE 80 443

# Добавляем healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -q --spider http://localhost/health || exit 1
