FROM nginx:alpine

# Копируем конфигурационные файлы
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/okypbot_locations.conf /etc/nginx/conf.d/okypbot_locations.conf

# Проверяем конфигурацию
RUN nginx -t

# Экспортируем порты
EXPOSE 80 443
