# TICKET-001: Базовая структура проекта

## Описание задачи
Создать базовую архитектуру проекта: конфигурацию, Pydantic-модели данных и FileManager для работы с Markdown-файлами.

## Компоненты для реализации
- `bot/config.py` - загрузка конфигурации из .env
- `bot/db/models.py` - Pydantic модели (InboxMessage, Task, Note)
- `bot/db/file_manager.py` - FileManager для работы с Markdown-файлами
- `.env` - файл конфигурации
- `requirements.txt` - зависимости проекта

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] Конфигурация загружается из .env переменных (TELEGRAM_BOT_TOKEN, OLLAMA_BASE_URL, OLLAMA_MODEL, DEFAULT_SUMMARIZE_DELAY)
- [ ] Pydantic модели валидируют данные правильно
- [ ] FileManager сохраняет и читает YAML-фронтмат в Markdown файлах
- [ ] Данные хранятся в структуре `data/{user_id}/{type}.md`
- [ ] Поддерживаются операции: append_message, read_messages, clear_messages, append_task, read_tasks, update_task_status, append_note, read_notes
- [ ] Формат файлов соответствует спецификации (YAML фронтмат + контент)

## Технические детали

### bot/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    DEFAULT_SUMMARIZE_DELAY: int = 300
```

### bot/db/models.py
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class InboxMessage(BaseModel):
    id: str
    timestamp: datetime
    from_user: int
    sender_id: int
    sender_name: Optional[str]
    content: str
    chat_id: int

class Task(BaseModel):
    id: str
    title: str
    tags: List[str]
    status: str = "pending"
    created_at: datetime
    source_message_ids: List[str]
    content: str

class Note(BaseModel):
    id: str
    title: str
    tags: List[str]
    created_at: datetime
    source_message_ids: List[str]
    content: str
```

### bot/db/file_manager.py
- `append_message(user_id, message)` - добавить сообщение в инбокс
- `read_messages(user_id)` - прочитать все сообщения
- `clear_messages(user_id)` - очистить инбокс
- `append_task(user_id, task)` - добавить задачу
- `read_tasks(user_id)` - прочитать задачи
- `update_task_status(task_id, status)` - обновить статус
- `append_note(user_id, note)` - добавить заметку
- `read_notes(user_id)` - прочитать заметки

## Требования к тестированию
- [ ] Unit-тесты для Settings: загрузка переменных окружения, значение по умолчанию для OLLAMA_BASE_URL
- [ ] Unit-тесты для Pydantic моделей: валидация обязательных полей, типизация, optional поля
- [ ] Unit-тесты для FileManager.append_message: создание файла, корректная запись YAML фронтмат
- [ ] Unit-тесты для FileManager.read_messages: чтение файла, парсинг YAML, создание объектов InboxMessage
- [ ] Unit-тесты для FileManager.clear_messages: очистка данных, сохранение структуры файла
- [ ] Unit-тесты для FileManager.append_task, read_tasks, update_task_status: создание, чтение, обновление задач
- [ ] Unit-тесты для FileManager.append_note, read_notes: создание, чтение заметок
- [ ] Integration-тесты: полный цикл работы с файлами (создать → прочитать → обновить → удалить)
- [ ] Проверка обработки ошибок: несуществующие файлы, повреждённый YAML, отсутствие прав доступа

## Обновление документации
- [ ] Если изменения затрагивают публичный API или архитектуру, обновить документацию
- [ ] Обновить README.md с новой информацией о функциональности
- [ ] Обновить документацию модулей в папке documentation/modules/

Формат файлов:
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