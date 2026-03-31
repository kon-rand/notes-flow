FROM python:3.12-slim

WORKDIR /app

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директорий
RUN mkdir -p data logs backup

# Настройка cron для ежедневного backup
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
COPY scripts/daily_backup.sh /usr/local/bin/daily_backup.sh
RUN chmod +x /usr/local/bin/daily_backup.sh
RUN (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/daily_backup.sh") | crontab -

# Запуск
CMD ["python", "-m", "bot.entrypoint"]