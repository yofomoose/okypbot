#!/bin/bash

# Создаем основные директории для постоянного хранения данных
sudo mkdir -p /var/lib/okypbot/postgres/data
sudo mkdir -p /var/lib/okypbot/postgres/backup
sudo mkdir -p /var/lib/okypbot/ml/models
sudo mkdir -p /var/lib/okypbot/ml/backups
sudo mkdir -p /var/lib/okypbot/ml/cache
sudo mkdir -p /var/lib/okypbot/logs
sudo mkdir -p /var/lib/okypbot/data

# Устанавливаем правильные права
sudo chown -R 999:999 /var/lib/okypbot/postgres  # 999 - postgres user
sudo chmod -R 700 /var/lib/okypbot/postgres/data  # Строгие права для данных
sudo chmod -R 755 /var/lib/okypbot/postgres/backup  # Права на чтение для бэкапов

# Права для остальных директорий
sudo chmod -R 777 /var/lib/okypbot/ml
sudo chmod -R 777 /var/lib/okypbot/logs
sudo chmod -R 777 /var/lib/okypbot/data

# Создаем файл для ротации бэкапов
cat << 'EOF' | sudo tee /etc/cron.daily/cleanup-postgres-backups
#!/bin/bash
find /var/lib/okypbot/postgres/backup -name "okypbot_*.sql" -mtime +7 -delete
EOF

sudo chmod +x /etc/cron.daily/cleanup-postgres-backups

echo "Директории созданы и права установлены"
echo "База данных будет сохраняться в /var/lib/okypbot/postgres/data"
echo "Бэкапы будут создаваться в /var/lib/okypbot/postgres/backup"
echo "Старые бэкапы (>7 дней) будут автоматически удаляться"
