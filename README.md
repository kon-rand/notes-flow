# Notes Flow

Telegram бот для управления заметками и задачами с AI-саммаризацией. Бот собирает сообщения из личных чатов, группирует связанные сообщения и автоматически создаёт задачи/заметки с помощью локальной AI-модели.

## Требования

- Python 3.12+
- Локальная AI-модель (OpenAI-compatible API)

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

2. Активируйте окружение:
```bash
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Установите типы для PyYAML (опционально, для mypy):
```bash
pip install types-PyYAML
```

5. Скопируйте `.env.example` в `.env` и настройте переменные окружения.

## Конфигурация

Создайте файл `.env` в корне проекта со следующими переменными:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DEFAULT_SUMMARIZE_DELAY=300
```

### Параметры конфигурации

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота от @BotFather | (обязательно) |
| `OLLAMA_BASE_URL` | URL AI API (OpenAI-compatible) | `http://localhost:8080` |
| `OLLAMA_MODEL` | Название модели для саммаризации | `unsloth/Qwen3.5-35B-A3B` |
| `DEFAULT_SUMMARIZE_DELAY` | Задержка перед саммаризацией в секундах | `300` (5 минут) |

## Запуск через Docker

### Локальный запуск (с Ollama на хосте)

```bash
docker-compose -f docker-compose.local.yml up -d
```

**Важно:**
- Используется `network_mode: host` для доступа к Ollama на `localhost:8080`
- Ollama должен быть запущен на хост-машине (не в контейнере)
- Данные хранятся в `/share/services/notes-flow/data` и `/share/services/notes-flow/logs`

### Просмотр логов

```bash
docker-compose -f docker-compose.local.yml logs -f
```

### Остановка

```bash
docker-compose -f docker-compose.local.yml down
```

### Запуск через Python (для разработки)

```bash
python bot/main.py
```

## Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и статистика |
| `/summarize` | Ручной запуск саммаризации |
| `/inbox` | Просмотр текущего инбокса |
| `/tasks` | Список задач |
| `/notes` | Список заметок |
| `/settings delay <minutes>` | Настройка задержки (в минутах) |
| `/clear inbox` | Очистка инбокса вручную |

### Примеры использования

**Отправка сообщений:**
```
Вы: Нужно подготовить отчёт по проекту
Вы: Вот данные для отчёта: [ссылка на файл]
```

Через 5 минут (или по таймеру) бот автоматически создаст задачу:
```
## task_001
title: Подготовить отчёт по проекту
tags: [работа, отчёт]
status: pending
created_at: 2026-03-06T14:40:00
source_message_ids: [msg_001, msg_002]
content:
- Собрать данные из файла
- Написать отчёт
- Сдать до завтра 10:00
```

**Обработка пересылок:**
```
Пользователь A пересылает сообщение от Пользователя B в бота

Запись в инбокс:
- from_user: A.id
- sender_id: B.id
- sender_name: "B.name"
- content: текст сообщения B
```

## Функции

### Основные
- ✅ Сбор сообщений из личных чатов (включая пересылки)
- ✅ Автоматическая саммаризация с настраиваемой задержкой
- ✅ Группировка связанных сообщений по времени и семантике
- ✅ Создание задач и заметок с тегами
- ✅ Хранение данных в Markdown-файлах с YAML-фронтматом
- ✅ Интеграция с AI-моделью через OpenAI-compatible API
- ✅ Поддержка пересылок с сохранением оригинального автора

### Управление
- ✅ Ручной запуск саммаризации по команде
- ✅ Просмотр инбокса, задач и заметок
- ✅ Настройка задержки саммаризации
- ✅ Очистка инбокса вручную

## Деплой

### Локальный деплой

1. Создайте директорию для данных:
```bash
sudo mkdir -p /share/services/notes-flow/data
sudo mkdir -p /share/services/notes-flow/logs
sudo chown -R $(whoami) /share/services/notes-flow
```

2. Запустите AI-модель с OpenAI-compatible API на `localhost:8080`

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env (TELEGRAM_BOT_TOKEN обязателен)
```

4. Запустите бот через Docker:
```bash
docker-compose -f docker-compose.local.yml up -d
```

5. Просмотр логов:
```bash
docker-compose -f docker-compose.local.yml logs -f
```

6. Остановка:
```bash
docker-compose -f docker-compose.local.yml down
```

**Примечание:** docker-compose.local.yml использует `network_mode: host` для доступа к API на `localhost:8080`.

### Облачный деплой

1. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env с URL удалённого API
```

2. Запустите бот:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Проверка статуса:
```bash
docker-compose -f docker-compose.prod.yml ps
```

4. Проверка healthcheck:
```bash
docker inspect notes-flow-prod --format='{{.State.Health.Status}}'
```

### Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота от @BotFather | (обязательно) |
| `OLLAMA_BASE_URL` | URL сервера Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Название модели для саммаризации | `llama3` |
| `DEFAULT_SUMMARIZE_DELAY` | Задержка перед саммаризацией в секундах | `300` (5 минут) |

### Хранение данных

Данные хранятся в структуре:
```
data/
└── {user_id}/
    ├── inbox.md      # Входящие сообщения
    ├── tasks.md      # Задачи
    └── notes.md      # Заметки
```

### Формат файлов

Каждый файл использует YAML-фронтмат:
```yaml
---
type: inbox
---

## msg_001
timestamp: 2026-03-06T14:30:00
from_user: 123456789
sender_id: 123456789
sender_name: null
content: Нужно подготовить отчёт по проекту
```

## Структура проекта

```
notes-flow/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── db/
│   │   ├── file_manager.py  # Работа с .md файлами
│   │   └── models.py        # Pydantic модели
│   └── timers/
│       └── manager.py       # Управление таймерами
├── handlers/
│   ├── commands.py          # Команды бота
│   ├── messages.py          # Обработка сообщений
│   └── summarizer.py        # Саммаризация
├── utils/
│   ├── ollama_client.py     # Ollama client
│   ├── context_analyzer.py  # Анализ контекста
│   └── markdown_parser.py   # Парсинг Markdown
├── data/                    # Хранение данных
├── tests/                   # Тесты
├── .env                     # Конфигурация
├── .env.example             # Пример конфигурации
├── .gitignore
├── requirements.txt
├── README.md
└── PLAN.md
```

## Тестирование

### Запуск всех тестов

```bash
pytest
```

### Запуск тестов для конкретного модуля

```bash
pytest tests/unit/bot/timers/
```

### Проверка типов

```bash
python3 -m mypy bot/ utils/ handlers/
```

### Статистика тестов

- Всего тестов: 131
- Unit тесты: 105
- Integration тесты: 31
- Mypy: 0 type errors

## Разработка

### Конвенции тестов

Следуйте [TEST_CONVENTIONS.md](TEST_CONVENTIONS.md) для написания тестов.

### Концепция работы агентов

Проект управляется командой агентов согласно [AGENTS.md](AGENTS.md).

## Критерии успеха

- [x] Сообщения сохраняются в Markdown с YAML-фронтмат
- [x] Пересылки корректно идентифицируются
- [x] Саммаризация запускается с задержкой и сбрасывается при новых сообщениях
- [x] Сообщения группируются по времени + семантике
- [x] Ollama создаёт задачи/заметки с тегами
- [x] Инбокс очищается после обработки
- [x] Данные хранятся раздельно по user_id
- [x] Доступны команды для ручного управления

## Зависимости

```
aiogram>=3.3.0
pydantic>=2.5.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
httpx>=0.25.0
```

## Лицензия

MIT