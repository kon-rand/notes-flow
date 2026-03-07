# Архитектура проекта Notes Flow

## Обзор

Notes Flow — это Telegram-бот для управления задачами и заметками с автоматической саммаризацией сообщений с помощью локальной LLM-модели (Ollama).

**Основные возможности:**
- Сбор сообщений из личных чатов (включая пересылки)
- Автоматическая группировка связанных сообщений
- Саммаризация с помощью локальной AI-модели
- Создание задач и заметок с тегами
- Хранение данных в Markdown-файлах с YAML-фронтматом

---

## Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         Telegram Bot                            │
│                         (aiogram 3.x)                           │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Bot Core                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ config.py   │  │ main.py     │  │ timers/manager.py       │ │
│  │ (Settings)  │  │ (DP setup)  │  │ (SummarizeTimer)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌───────────────┐ ┌───────────────────────┐
│   Handlers Module    │ │  Utils Module  │ │      DB Module        │
│ ┌───────────────────┐ │ ┌─────────────┐ │ │ ┌───────────────────┐ │
│ │ messages.py       │ │ │ context_    │ │ │ │ file_manager.py   │ │
│ │ (message handler) │ │ │ analyzer.py │ │ │ │ (FileManager)     │ │
│ ├───────────────────┤ │ ├─────────────┤ │ │ ├───────────────────┤ │
│ │ commands.py       │ │ │ ollama_     │ │ │ │ models.py         │ │
│ │ (/start, /help,   │ │ │ client.py   │ │ │ │ (Pydantic models) │ │
│ │  /summarize, etc) │ │ └─────────────┘ │ │ └───────────────────┘ │
│ └───────────────────┘ │ └─────────────┘ │ └───────────────────┘ │
│ ┌───────────────────┐ │ └─────────────┘ │ └───────────────────┘ │
│ │ summarizer.py     │ │                 │                       │
│ │ (auto_summarize)  │ │                 │                       │
│ └───────────────────┘ │                 │                       │
└───────────────────────┘                 │                       │
                                          ▼                       ▼
                              ┌─────────────────────┐   ┌─────────────────┐
                              │   Ollama API        │   │  Data Directory │
                              │   http://localhost: │   │  data/{user_id}/│
                              │   11434/api/generate│   │  ├── inbox.md  │
                              └─────────────────────┘   │  ├── tasks.md  │
                                                        │  └── notes.md  │
                                                        └─────────────────┘
```

---

## Модули системы

### [Bot Core](modules/bot.md)
Ядро бота — настройка aiogram, диспетчер событий, управление таймерами.

### [Handlers](modules/handlers.md)
Обработчики сообщений и команд Telegram.

### [Utils](modules/utils.md)
Вспомогательные модули: анализ контекста, работа с Ollama.

### [DB](modules/db.md)
Файловое хранилище данных в формате Markdown.

### [Config](modules/config.md)
Конфигурация приложения (переменные окружения).

### [Models](modules/models.md)
Pydantic модели данных.

---

## Потоки данных

### Обработка входящего сообщения

```
┌────────────┐     ┌─────────────┐     ┌──────────────────┐
│ Telegram   │────▶│  Handlers   │────▶│  FileManager     │
│  Message   │     │ messages.py │     │  append_message  │
└────────────┘     └─────────────┘     └──────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  data/{user_id}/ │
                                    │  inbox.md        │
                                    └──────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  SummarizeTimer  │
                                    │  (async delay)   │
                                    └──────────────────┘
```

### Саммаризация

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  SummarizeTimer  │────▶│  Summarizer      │────▶│  ContextAnalyzer │
│  (timeout)       │     │  auto_summarize  │     │  group_messages  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐     ┌────────────┐
                                    │  OllamaClient    │────▶│  LLM API   │
                                    │  summarize_group │     │            │
                                    └──────────────────┘     └────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐     ┌──────────────────┐
                                    │  FileManager     │────▶│  data/{user_id}/ │
                                    │  append_task/note│     │  tasks.md/notes.md│
                                    └──────────────────┘     └──────────────────┘
```

---

## Структура проекта

```
notes-flow/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Settings (Pydantic)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic models
│   │   └── file_manager.py    # FileManager
│   └── timers/
│       └── manager.py         # SummarizeTimer
├── handlers/
│   ├── __init__.py
│   ├── commands.py            # Команды бота
│   ├── messages.py            # Обработка сообщений
│   └── summarizer.py          # Саммаризация
├── utils/
│   ├── __init__.py
│   ├── context_analyzer.py    # ContextAnalyzer
│   └── ollama_client.py       # OllamaClient
├── data/
│   └── {user_id}/
│       ├── inbox.md           # Входящие сообщения
│       ├── tasks.md           # Задачи
│       └── notes.md           # Заметки
├── documentation/
│   ├── ARCHITECTURE.md
│   └── modules/
│       ├── bot.md
│       ├── handlers.md
│       ├── utils.md
│       ├── db.md
│       ├── config.md
│       └── models.md
├── .env                       # Конфигурация
├── requirements.txt
└── README.md
```

---

## Модели данных

### InboxMessage
```python
class InboxMessage(BaseModel):
    id: str                    # Уникальный ID (message_id)
    timestamp: datetime
    from_user: int             # Пользователь, отправивший сообщение боту
    sender_id: int             # Оригинальный автор (для пересылок)
    sender_name: Optional[str] # Имя отправителя
    content: str               # Текст сообщения
    chat_id: int
```

### Task
```python
class Task(BaseModel):
    id: str
    title: str
    tags: List[str]
    status: str = "pending"    # pending, completed
    created_at: datetime
    source_message_ids: List[str]
    content: str
```

### Note
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

## Конфигурация

Переменные окружения (`.env`):

```env
TELEGRAM_BOT_TOKEN=your_token_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DEFAULT_SUMMARIZE_DELAY=300
```

---

## Обработка пересылок

При получении пересланного сообщения извлекается информация об оригинальном авторе:

```
Пользователь A пересылает сообщение от Пользователя B в бота

Запись в инбокс:
- from_user: A.id (тот, кто переслал)
- sender_id: B.id (оригинальный автор)
- sender_name: "B.name"
- content: текст сообщения B
```

Типы пересылок:
- `MessageOriginUser` — от пользователя
- `MessageOriginHiddenUser` — от скрытого пользователя
- `MessageOriginChat` — от чата/канала

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

**Версия документа**: 1.0  
**Дата обновления**: 2026-03-07