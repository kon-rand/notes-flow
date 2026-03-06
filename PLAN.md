# Telegram Bot для заметок и задач с AI-саммаризацией

## Описание
Бот собирает сообщения из личных чатов, группирует связанные сообщения и автоматически создаёт задачи/заметки с помощью локальной AI-модели.

## Целевая функциональность
- Сбор сообщений из личных чатов (включая пересылки)
- Автоматическая саммаризация с задержкой (настраиваемой)
- Группировка связанных сообщений по времени и семантике
- Создание задач и заметок с тегами
- Хранение данных в Markdown-файлах с YAML-фронтматом

---

## Структура проекта

```
notes-flow/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа, инициализация DP
│   ├── config.py            # Конфигурация (.env)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── file_manager.py  # FileManager - работа с .md
│   │   └── models.py        # Pydantic модели (Message, Task, Note)
│   └── timers/
│       └── manager.py       # SummarizeTimer - управление задержками
├── handlers/
│   ├── __init__.py
│   ├── commands.py          # /start, /summarize, /settings, /inbox, /tasks, /notes
│   ├── messages.py          # Обработка входящих сообщений
│   └── summarizer.py        # Запуск саммаризации
├── utils/
│   ├── __init__.py
│   ├── ollama_client.py     # OllamaClient - запросы к LLM
│   ├── context_analyzer.py  # ContextAnalyzer - группировка сообщений
│   └── markdown_parser.py   # Парсинг YAML-фронтмат
├── data/
│   └── {user_id}/
│       ├── inbox.md
│       ├── tasks.md
│       └── notes.md
├── .env                     # TELEGRAM_BOT_TOKEN, OLLAMA_BASE_URL, DEFAULT_DELAY
├── .gitignore
└── requirements.txt
```

---

## Модели данных (Pydantic)

### InboxMessage (входящее сообщение)
```python
class InboxMessage(BaseModel):
    id: str                    # Уникальный ID сообщения
    timestamp: datetime
    from_user: int             # user_id (originator)
    sender_id: int             # фактический отправитель (если пересылка)
    sender_name: str | None
    content: str
    chat_id: int
```

### Task (задача)
```python
class Task(BaseModel):
    id: str
    title: str
    tags: List[str]
    status: str = "pending"    # pending, completed
    created_at: datetime
    source_message_ids: List[str]  # ссылки на сообщения в инбоксе
    content: str
```

### Note (заметка)
```python
class Note(BaseModel):
    id: str
    title: str
    tags: List[str]
    created_at: datetime
    source_message_ids: List[str]
    content: str
```

---

## Ключевые компоненты

### FileManager (bot/db/file_manager.py)
Работа с Markdown-файлами:
- `append_message(user_id, message)` - добавить сообщение в инбокс
- `read_messages(user_id)` - прочитать все сообщения
- `clear_messages(user_id)` - очистить инбокс
- `append_task(user_id, task)` - добавить задачу
- `read_tasks(user_id)` - прочитать задачи
- `update_task_status(task_id, status)` - обновить статус
- `append_note(user_id, note)` - добавить заметку
- `read_notes(user_id)` - прочитать заметки

**Путь к файлам**: `data/{user_id}/{type}.md`

### ContextAnalyzer (utils/context_analyzer.py)
Группировка связанных сообщений:
- `group_messages(messages)` - главная функция группировки
- `_group_by_time_window(messages, window_minutes=30)` - по времени
- `_group_by_similarity(messages)` - по семантике (ключевые слова)
- `detect_continuation(current, previous)` - поиск ссылок на предыдущие

**Признаки связанности**:
1. Временная близость (≤ 30 минут)
2. Общие ключевые слова (≥ 3 совпадения)
3. Упоминания продолжения ("как я говорил", "ещё по теме")

### OllamaClient (utils/ollama_client.py)
Запросы к локальной модели:
- `summarize_group(messages)` - анализ группы сообщений
- Возвращает JSON с решением: `create_task`, `create_note`, или `skip`

**Параметры**:
- BASE_URL: `http://localhost:11434`
- MODEL: `llama3` (или из .env)

### SummarizeTimer (bot/timers/manager.py)
Управление задержкой:
- `schedule_summarization(user_id, delay_seconds)` - запланировать
- `reset(user_id)` - сброс при новом сообщении
- `_wait_and_summarize(user_id, delay)` - асинхронный таймер

---

## Промпты для Ollama

### Для задач
```
Ты помощник для управления задачами. Проанализируй эти сообщения:

{messages_text}

Если есть действия, которые нужно выполнить:
- Создай задачу с чётким названием
- Добавь до 3 тегов
- Укажи все детали в content

Формат JSON:
{
  "action": "create_task",
  "title": "Краткое название задачи",
  "tags": ["tag1", "tag2"],
  "content": "Полное описание",
  "reason": "Почему это задача"
}

Если это не задача - верни: {"action": "skip"}
```

### Для заметок
```
Ты помощник для хранения информации. Проанализируй:

{messages_text}

Если есть ценная информация для сохранения:
- Создай заметку с заголовком
- Добавь теги для категоризации
- Сохрани суть в content

Формат JSON:
{
  "action": "create_note",
  "title": "Название заметки",
  "tags": ["tag1", "tag2"],
  "content": "Контент заметки",
  "reason": "Почему это стоит сохранить"
}

Иначе: {"action": "skip"}
```

---

## Поток обработки

### Обработка сообщения
1. **[handlers/messages.py: message_handler]**
   - Извлечь `user_id` (`message.from_user.id`)
   - Если `forward` → извлечь `forward_author_id`
   - Создать `InboxMessage`
   - `FileManager.append_message(user_id, message)`

2. **[SummarizeTimer.schedule_summarization]**
   - Cancel previous timer
   - Start new timer (`asyncio.sleep(delay)`)

### Саммаризация (по истечению задержки)
1. **[handlers/summarizer.py: auto_summarize]**
   - `FileManager.read_messages(user_id)`
   - `ContextAnalyzer.group_messages(messages)`
   - Для каждой группы:
     - `OllamaClient.summarize_group(group)`
     - `FileManager.append_task` ИЛИ `FileManager.append_note`
   - `FileManager.clear_messages(user_id)`
   - Отправка отчёта в чат

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие, статистика |
| `/summarize` | Ручной запуск саммаризации |
| `/inbox` | Просмотр текущего инбокса |
| `/tasks` | Список задач (с `/task done <id>`) |
| `/notes` | Список заметок |
| `/settings delay <minutes>` | Настройка задержки |
| `/clear inbox` | Очистка инбокса вручную |

---

## Конфигурация (.env)

```env
TELEGRAM_BOT_TOKEN=your_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DEFAULT_SUMMARIZE_DELAY=300  # 5 минут в секундах
```

---

## Зависимости (requirements.txt)

```
aiogram>=3.3.0
pydantic>=2.5.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
httpx>=0.25.0
```

---

## Тикеты для агентов

| # | Тикет | Статус | Описание |
|---|-------|--------|----------|
| 1 | TICKET-001.md | ✅ | Базовая структура (config.py, models.py, FileManager) |
| 2 | TICKET-002.md | ✅ | Обработка сообщений (handlers/messages.py) |
| 3 | TICKET-003.md | ✅ | Таймеры (SummarizeTimer) |
| 4 | TICKET-004.md | ✅ | Контекстный анализ (ContextAnalyzer) |
| 5 | TICKET-005.md | ✅ | Ollama интеграция (utils/ollama_client.py) |
| 6 | TICKET-006.md | ✅ | Саммаризатор (handlers/summarizer.py) |
| 7 | TICKET-007.md | ✅ | Команды бота (handlers/commands.py) |
| 8 | TICKET-008.md | ⏳ | Обработка пересылок (forward_origin parsing) |
| 9 | TICKET-009.md | ⏳ | Тестирование и полировка |

**Статусы**: ⏳ pending, ✅ completed, 🚧 in_progress

## Этапы реализации

| # | Этап | Компоненты | Приоритет |
|---|------|------------|-----------|
| 1 | Базовая структура | config.py, models.py, FileManager | 🔴 |
| 2 | Обработка сообщений | handlers/messages.py, FileManager.append_message | 🔴 |
| 3 | Таймеры | SummarizeTimer, handlers/commands.py | ✅ |
| 4 | Контекстный анализ | utils/context_analyzer.py | 🔴 |
| 5 | Ollama интеграция | utils/ollama_client.py | 🔴 |
| 6 | Саммаризатор | handlers/summarizer.py | 🔴 |
| 7 | Команды | handlers/commands.py (/summarize, /inbox, /tasks, /notes, /settings) | 🟡 |
| 8 | Обработка пересылок | forward_origin parsing | 🔴 |
| 9 | Тестирование и полировка | - | 🟡 |

---

## Формат хранения данных

### Пример inbox.md
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

---
## msg_002
timestamp: 2026-03-06T14:35:00
from_user: 123456789
sender_id: 123456789
sender_name: null
content: Вот данные для отчёта: [ссылка на файл]
```

### Пример tasks.md
```yaml
---
type: task
---

## task_001
title: Подготовить отчёт по проекту
tags: [работа, отчёт]
status: pending
created_at: 2026-03-06T14:40:00
source_message_ids: [msg_001, msg_002, msg_003]
content: 
- Собрать данные из файла
- Написать отчёт
- Сдать до завтра 10:00
```

### Пример notes.md
```yaml
---
type: note
---

## note_001
title: Идеи для проекта
tags: [идеи, разработка]
created_at: 2026-03-06T14:40:00
source_message_ids: [msg_004]
content: Предложено использовать async/await для обработки сообщений
```

---

## Обработка пересылок

При получении пересланного сообщения:
1. Извлечь `message.forward_origin`
2. Определить тип: `ForwardOriginUser`, `ForwardOriginHiddenUser`, `ForwardOriginChat`
3. Записать в инбокс:
   - `from_user` = `message.from_user.id` (тот, кто переслал)
   - `sender_id` = `forward_author_id` (оригинальный автор)
   - `sender_name` = имя оригинального автора

Пример:
```
Пользователь A пересылает сообщение от Пользователя B в бота

Запись в инбокс:
- from_user: A.id
- sender_id: B.id
- sender_name: "B.name"
- content: текст сообщения B
```

---

## Критерии успеха

- [x] Сообщения сохраняются в Markdown с YAML-фронтмат
- [x] Пересылки корректно идентифицируются
- [x] Саммаризация запускается с задержкой и сбрасывается при новых сообщениях
- [x] Сообщения группируются по времени + семантике
- [x] Ollama создаёт задачи/заметки с тегами
- [x] Инбокс очищается после обработки
- [x] Данные хранятся раздельно по user_id
- [x] Доступны команды для ручного управления

---

**План составлен**: 2026-03-06
**Версия**: 1.0