# Деплой Notes Flow

## Обзор

Документ описывает процесс деплоя Telegram бота Notes Flow через Docker Compose.

## Требования

- Docker Engine 20.10+
- Docker Compose 2.0+
- Для локального деплоя: Ollama на localhost:11434
- Для продакшена: доступный Ollama сервер

## Локальный деплой

### Подготовка

1. Создайте директорию для хранения данных:
```bash
sudo mkdir -p /share/services/notes-flow/data
sudo mkdir -p /share/services/notes-flow/logs
sudo chown -R $(whoami) /share/services/notes-flow
```

2. Настройте переменные окружения:
```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DEFAULT_SUMMARIZE_DELAY=300
```

### Запуск

```bash
docker-compose -f docker-compose.local.yml up -d
```

### Управление

**Просмотр логов:**
```bash
docker-compose -f docker-compose.local.yml logs -f
```

**Остановка:**
```bash
docker-compose -f docker-compose.local.yml down
```

**Перезапуск:**
```bash
docker-compose -f docker-compose.local.yml restart
```

### Структура volumes

| Путь на хосте | В контейнере | Назначение |
|---------------|--------------|------------|
| `/share/services/notes-flow/data` | `/app/data` | Данные пользователей |
| `/share/services/notes-flow/logs` | `/app/logs` | Логи (опционально) |
| `ollama-data` (Docker volume) | `/root/.ollama` | Модели Ollama |

## Облачный деплой

### Подготовка

1. Настройте переменные окружения:
```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OLLAMA_BASE_URL=https://your-ollama-server.com
OLLAMA_MODEL=llama3
DEFAULT_SUMMARIZE_DELAY=300
```

### Запуск

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Управление

**Просмотр статуса:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

**Проверка healthcheck:**
```bash
docker inspect notes-flow-prod --format='{{.State.Health.Status}}'
```

**Просмотр логов:**
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Остановка:**
```bash
docker-compose -f docker-compose.prod.yml down
```

### Структура volumes

| Volume | В контейнере | Назначение |
|--------|--------------|------------|
| `notes-flow-data` (Docker volume) | `/app/data` | Данные пользователей |

### Healthcheck

Healthcheck проверяет наличие процесса бота:

```yaml
healthcheck:
  test: ["CMD", "pgrep", "-f", "main"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Restart policy

```yaml
restart: always
```

Контейнер автоматически перезапускается при:
- Падении процесса
- Перезагрузке хоста
- Ошибке Docker daemon

## Dockerfile

### Структура

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директорий
RUN mkdir -p data logs

# Запуск
CMD ["python", "-m", "bot.main"]
```

### Оптимизации

- Base image `python:3.12-slim` для минимального размера
- `--no-cache-dir` для уменьшения размера image
- Разделение копирования `requirements.txt` и кода для кэширования слоев

## .dockerignore

Исключает ненужные файлы из image:

```
.env
data/
*.md
!Dockerfile
tests/
__pycache__/
*.pyc
.git/
.idea/
*.log
venv/
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
```

## Переменные окружения

| Переменная | Описание | По умолчанию | Обязательная |
|------------|----------|--------------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | - | Да |
| `OLLAMA_BASE_URL` | URL сервера Ollama | `http://localhost:11434` | Нет |
| `OLLAMA_MODEL` | Название модели | `llama3` | Нет |
| `DEFAULT_SUMMARIZE_DELAY` | Задержка саммаризации (сек) | `300` | Нет |

## Troubleshooting

### Контейнер не запускается

**Проверка логов:**
```bash
docker-compose -f docker-compose.local.yml logs
```

**Проблема с permission:**
```bash
sudo chown -R $(whoami) /share/services/notes-flow
```

### Ollama недоступен

**Проверка статуса:**
```bash
docker-compose -f docker-compose.local.yml ps ollama
```

**Проверка доступности:**
```bash
curl http://localhost:11434/api/tags
```

### Healthcheck не проходит

**Проверка процесса:**
```bash
docker exec notes-flow-prod pgrep -f main
```

**Перезапуск:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

## Безопасность

### Secrets

Для продакшена рекомендуется использовать Docker secrets:

```yaml
services:
  notes-flow:
    secrets:
      - telegram_token
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

secrets:
  telegram_token:
    file: ./secrets/telegram_token.txt
```

### Переменные окружения

Никогда не коммитьте `.env` файл:
```bash
echo ".env" >> .gitignore
```

## Производительность

### Настройка ресурсов

Для продакшена можно ограничить ресурсы:

```yaml
services:
  notes-flow:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### Логирование

Настройте драйвер логирования для продакшена:

```yaml
services:
  notes-flow:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## CI/CD интеграция

### GitHub Actions пример

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and deploy
        run: |
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml up -d
```

## Обновление

### Обновление image

```bash
docker-compose -f docker-compose.local.yml pull
docker-compose -f docker-compose.local.yml up -d
```

### Откат версии

```bash
# Редактировать docker-compose.yml с указанием версии image
docker-compose -f docker-compose.local.yml up -d
```

## Миграция данных

### Перенос данных между серверами

```bash
# Экспорт данных
docker exec notes-flow-prod tar czf /tmp/data.tar.gz /app/data

# Скачивание
docker cp notes-flow-prod:/tmp/data.tar.gz ./data.tar.gz

# Импорт на новый сервер
docker cp data.tar.gz notes-flow-new:/tmp/
docker exec notes-flow-new tar xzf /tmp/data.tar.gz -C /
```

## Ссылки

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Ollama Documentation](https://github.com/ollama/ollama)