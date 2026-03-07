# Деплой через Docker Compose

## Описание задачи

Реализовать два Docker Compose конфигура для деплоя бота:
1. **Локальный деплой** - для разработки и тестирования
2. **Облачный деплой** - для продакшена

## Требования

### Локальный деплой

- Использовать `docker-compose.local.yml`
- Хранить данные пользователей на хосте в `/share/services/notes-flow/`
- Монтировать volumes:
  - `/share/services/notes-flow/data` → `/app/data`
  - `/share/services/notes-flow/logs` → `/app/logs` (опционально)
- Ожидать Ollama на `http://localhost:11434`
- Запускать через `docker-compose -f docker-compose.local.yml up`

### Облачный деплой

- Использовать `docker-compose.prod.yml`
- Включить healthcheck для мониторинга
- Настроить restart policy: `always`
- Хранить данные внутри контейнера (volume: `notes-flow-data`)
- Ожидать внешний сервис Ollama по переменной окружения
- Использовать secrets для чувствительных данных (опционально)

## Компоненты для реализации

### 1. Dockerfile
- Base image: `python:3.12-slim`
- Рабочая директория: `/app`
- Копирование `requirements.txt` и установка зависимостей
- Копирование исходного кода
- CMD для запуска бота

### 2. docker-compose.local.yml
```yaml
version: '3.8'
services:
  notes-flow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: notes-flow-local
    volumes:
      - /share/services/notes-flow/data:/app/data
      - /share/services/notes-flow/logs:/app/logs
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OLLAMA_BASE_URL=http://localhost:11434
      - OLLAMA_MODEL=llama3
      - DEFAULT_SUMMARIZE_DELAY=300
    restart: unless-stopped
    depends_on:
      - ollama
    ports:
      - "8000:8000"  # для отладки, если нужно

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-local
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama-data:
```

### 3. docker-compose.prod.yml
```yaml
version: '3.8'
services:
  notes-flow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: notes-flow-prod
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3}
      - DEFAULT_SUMMARIZE_DELAY=${DEFAULT_SUMMARIZE_DELAY:-300}
    restart: always
    healthcheck:
      test: ["CMD", "pgrep", "-f", "main"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - notes-flow-data:/app/data

volumes:
  notes-flow-data:
```

### 4. .dockerignore
- `.env`
- `data/`
- `*.md` (кроме Dockerfile)
- `tests/`
- `__pycache__/`
- `*.pyc`
- `.git/`
- `.idea/`
- `*.log`

### 5. Обновление документации
- README.md - добавить секцию "Деплой"
- documentation/DEPLOYMENT.md - детальное описание деплоя
- AGENTS.md - обновить статус тикета
- PLAN.md - обновить статус тикета

## Технические детали

### Структура Dockerfile

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

### Обработка переменных окружения

- Использовать `.env.example` для примера конфигурации
- В локальном режиме: `.env` читается docker-compose автоматически
- В продакшене: переменные передаются через CI/CD или вручную

### Healthcheck

- Проверка процесса бота через `pgrep`
- Интервал: 30 секунд
- Таймаут: 10 секунд
- Retry: 3 попытки

### Volumes и持久нные данные

**Локальный деплой:**
- Данные пользователей: `/share/services/notes-flow/data` на хосте
- Логи: `/share/services/notes-flow/logs` на хосте
- Ollama модели: `ollama-data` (Docker volume)

**Облачный деплой:**
- Данные пользователей: `notes-flow-data` (Docker volume)
- Ollama: внешний сервис (не в контейнере)

## Примеры использования

### Локальный запуск

```bash
# Создание директории для данных
sudo mkdir -p /share/services/notes-flow/data
sudo mkdir -p /share/services/notes-flow/logs
sudo chown -R $(whoami) /share/services/notes-flow

# Запуск бота
docker-compose -f docker-compose.local.yml up -d

# Просмотр логов
docker-compose -f docker-compose.local.yml logs -f

# Остановка
docker-compose -f docker-compose.local.yml down
```

### Облачный запуск

```bash
# Создание .env файла с переменными
cp .env.example .env
# Редактировать .env

# Деплой
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр healthcheck
docker inspect notes-flow-prod --format='{{.State.Health.Status}}'
```

## Тестирование

### Проверка локального деплоя

1. Запустить `docker-compose -f docker-compose.local.yml up`
2. Убедиться что бот получает сообщения
3. Проверить что файлы создаются в `/share/services/notes-flow/data/{user_id}/`
4. Проверить что Ollama доступен по `http://localhost:11434`
5. Протестировать команды бота: `/start`, `/summarize`, `/tasks`

### Проверка облачного деплоя

1. Запустить `docker-compose -f docker-compose.prod.yml up -d`
2. Проверить healthcheck через `docker inspect`
3. Убедиться что контейнер перезапускается при падении
4. Проверить что данные сохраняются в volume

## Критерии успеха

- [x] Dockerfile создан и работает
- [x] docker-compose.local.yml настроен для локального деплоя
- [x] docker-compose.prod.yml настроен для облачного деплоя
- [x] Volumes смонтированы корректно
- [x] Healthcheck работает в продакшене
- [x] .dockerignore исключает лишние файлы
- [x] Документация обновлена (README.md, DEPLOYMENT.md)
- [x] Тесты проходят

## Обновление документации

После реализации обновить:
1. **README.md** - добавить секцию "Деплой" с примерами
2. **documentation/DEPLOYMENT.md** - детальное описание
3. **AGENTS.md** - обновить статус тикета в таблице
4. **PLAN.md** - добавить TICKET-011 и обновить статус

## Связанные тикеты

- TICKET-001 - Базовая структура
- TICKET-010 - Документация архитектуры