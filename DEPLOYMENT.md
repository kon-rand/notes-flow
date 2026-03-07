# Запуск и эксплуатация Notes Flow

## Быстрый старт

### Требования

- Docker
- Docker Compose
- Python 3.12+ (для локального запуска)
- Ollama (опционально, для саммаризации)

### Настройка

1. **Копирование конфигурации:**
   ```bash
   cp .env.example .env
   ```

2. **Редактирование .env:**
   ```bash
   nano .env
   ```
   
   Добавьте токен вашего бота:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

### Запуск через Docker Compose

```bash
# Запуск в фоновом режиме
docker-compose -f docker-compose.local.yml up -d

# Пересборка образа
docker-compose -f docker-compose.local.yml build

# Перезапуск
docker-compose -f docker-compose.local.yml restart
```

### Локальный запуск (без Docker)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
python -m bot.main
```

## Просмотр логов

### Docker Compose

```bash
# Просмотр всех логов в реальном времени
docker-compose -f docker-compose.local.yml logs -f

# Просмотр логов конкретного контейнера
docker logs -f notes-flow-local

# Просмотр последних 100 строк
docker-compose -f docker-compose.local.yml logs --tail=100
```

### Локальный запуск

Логи выводятся в консоль. Для сохранения в файл:

```bash
python -m bot.main > logs/bot.log 2>&1
```

## Остановка

```bash
# Остановка контейнера
docker-compose -f docker-compose.local.yml down

# Остановка с удалением volumes (данные будут потеряны)
docker-compose -f docker-compose.local.yml down -v
```

## Отладка

### Проверка статуса

```bash
# Статус контейнеров
docker-compose -f docker-compose.local.yml ps

# Проверка работы контейнера
docker-compose -f docker-compose.local.yml exec notes-flow pgrep -f "python.*main"
```

### Вход в контейнер

```bash
docker-compose -f docker-compose.local.yml exec notes-flow bash
```

### Запуск бота вручную внутри контейнера

```bash
docker-compose -f docker-compose.local.yml exec notes-flow python -m bot.main
```

### Проверка данных

```bash
# Просмотр файлов данных
docker-compose -f docker-compose.local.yml exec notes-flow ls -la /app/data/

# Просмотр содержимого файла
docker-compose -f docker-compose.local.yml exec notes-flow cat /app/data/{user_id}/tasks.md
```

## Структура данных

### Директории

| Путь в контейнере | Путь на хосте | Описание |
|------------------|---------------|----------|
| `/app/data` | `/share/services/notes-flow/data` | Данные пользователей |
| `/app/logs` | `/share/services/notes-flow/logs` | Логи бота |

### Файлы пользователей

Для каждого пользователя создаётся директория `data/{user_id}/`:

- `inbox.md` - входящие сообщения
- `tasks.md` - задачи
- `notes.md` - заметки

### Формат данных

Файлы используют формат YAML:

```yaml
# tasks.md
- id: task_001
  title: Купить продукты
  status: pending
  tags: [покупки, дом]
  content: Молоко, хлеб, яйца
  source_message_ids: ["123", "124"]
  created_at: "2026-03-07T10:30:00"
```

## Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|-----------|-------------|--------------|----------|
| `TELEGRAM_BOT_TOKEN` | Да | - | Токен бота от @BotFather |
| `OLLAMA_BASE_URL` | Нет | `http://127.0.0.1:8080/v1` | URL Ollama API |
| `OLLAMA_MODEL` | Нет | `unsloth/Qwen3.5-35B-A3B` | Модель для саммаризации |
| `DEFAULT_SUMMARIZE_DELAY` | Нет | `300` | Задержка саммаризации в секундах |

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Показать статистику и приветствие |
| `/help` | Показать список команд |
| `/inbox` | Просмотр текущего инбокса |
| `/tasks` | Список всех задач |
| `/notes` | Список всех заметок |
| `/summarize` | Ручная саммаризация инбокса |
| `/settings delay <мин>` | Настройка задержки саммаризации |
| `/clear inbox` | Очистка инбокса |

## Решение проблем

### Бот не запускается

1. **Проверьте логи:**
   ```bash
   docker-compose -f docker-compose.local.yml logs
   ```

2. **Проверьте токен:**
   ```bash
   docker-compose -f docker-compose.local.yml exec notes-flow env | grep TELEGRAM
   ```

3. **Проверьте Ollama (если используется):**
   ```bash
   curl http://127.0.0.1:8080/api/tags
   ```

### Ошибки импорта

Если видите ошибки типа `ModuleNotFoundError`:

```bash
# Пересоберите образ
docker-compose -f docker-compose.local.yml build --no-cache

# Проверьте requirements.txt
docker-compose -f docker-compose.local.yml exec notes-flow pip list
```

### Проблемы с правами доступа к Docker

```bash
# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Обновите группу (требует выхода/входа)
newgrp docker
```

### Бот не отвечает на команды

1. Проверьте, что бот запущен:
   ```bash
   docker-compose -f docker-compose.local.yml ps
   ```

2. Проверьте подключение к Telegram:
   ```bash
   docker-compose -f docker-compose.local.yml logs | grep "Starting bot"
   ```

3. Перезапустите бота:
   ```bash
   docker-compose -f docker-compose.local.yml restart
   ```

## Мониторинг

### Использование ресурсов

```bash
# Потребление ресурсов контейнером
docker-compose -f docker-compose.local.yml stats

# Информация о контейнере
docker-compose -f docker-compose.local.yml inspect notes-flow
```

### Проверка здоровья

```bash
# Проверка процесса бота
docker-compose -f docker-compose.local.yml exec notes-flow pgrep -f "python.*main"

# Проверка файлов данных
docker-compose -f docker-compose.local.yml exec notes-flow ls -la /app/data/
```

## Бэкап данных

```bash
# Создание бэкапа
docker-compose -f docker-compose.local.yml exec notes-flow tar czf /tmp/backup.tar.gz /app/data/
docker cp notes-flow:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz

# Восстановление
docker cp backup.tar.gz notes-flow:/tmp/backup.tar.gz
docker-compose -f docker-compose.local.yml exec notes-flow tar xzf /tmp/backup.tar.gz -C /
```

## Обновление

```bash
# Pull новых образов
docker-compose -f docker-compose.local.yml pull

# Пересборка
docker-compose -f docker-compose.local.yml build

# Перезапуск
docker-compose -f docker-compose.local.yml up -d
```

## Дополнительные ресурсы

- [Документация aiogram](https://docs.aiogram.dev/)
- [Документация Docker](https://docs.docker.com/)
- [Документация Ollama](https://github.com/ollama/ollama)