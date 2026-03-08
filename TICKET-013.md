# TICKET-013: Исправление саммаризатора

## Название этапа
Исправление обработки пересылок и саммаризации

## Описание задачи
Бот некорректно обрабатывает пересылаемые сообщения — они не попадают в inbox и не создаются задачи из них. Необходимо исправить логику обработки `message.forwarded` и убедиться, что все сообщения корректно обрабатываются.

## Приоритет
🟡 средний

## Компоненты для реализации

### 1. Анализ текущей проблемы
- Проверить, как обрабатываются forwarded сообщения
- Найти место, где сообщения пропускаются
- Проверить логи обработки в `handlers/messages.py`

### 2. Исправление обработки пересылок
- Убедиться, что forwarded сообщения тоже добавляются в inbox
- Проверить обработку `message.forwarded` атрибута
- Добавить логи для отладки

### 3. Тестирование
- Написать тесты для forwarded сообщений
- Проверить, что сообщения корректно сохраняются
- Протестировать саммаризацию с forwarded сообщениями

## Технические детали

### Проблема с обработкой пересылок

**Текущий код в `handlers/messages.py`:**
```python
@router.message(F.text)
async def handle_message(message: Message):
    """Обработка входящих сообщений."""
    user_id = message.from_user.id
    text = message.text
    
    # Сохраняем в inbox
    await db.add_to_inbox(user_id, text)
    
    # Создаем задачу, если это вопрос
    if is_task_question(text):
        await db.add_task(user_id, text)
```

**Проблема:** Код не проверяет `message.forwarded`, поэтому forwarded сообщения могут обрабатываться некорректно.

**Решение:**
```python
@router.message(F.text)
async def handle_message(message: Message):
    """Обработка входящих сообщений."""
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем, это forwarded сообщение?
    is_forwarded = message.forwarded is not None
    
    # Сохраняем в inbox
    await db.add_to_inbox(user_id, text, is_forwarded=is_forwarded)
    
    # Создаем задачу, если это вопрос
    if is_task_question(text):
        await db.add_task(user_id, text)
```

### Примеры forwarded сообщений

**Telegram API структура forwarded сообщения:**
```python
message.forwarded = {
    "date": 1234567890,
    "from": {"id": 123, "is_bot": False, "first_name": "User"},
    "chat": {"id": 456, "type": "private", "title": "User"},
    "text": "Текст сообщения"
}
```

### Тесты

**Тест для forwarded сообщений:**
```python
async def test_forwarded_message_handling():
    """Тест обработки пересылаемых сообщений."""
    # Создаем mock forwarded message
    from unittest.mock import MagicMock
    
    mock_message = MagicMock()
    mock_message.text = "Пересланное сообщение"
    mock_message.from_user.id = 123
    mock_message.forwarded = {"date": 1234567890, "from": {"id": 456}}
    
    # Вызываем handler
    await handle_message(mock_message)
    
    # Проверяем, что сообщение добавлено в inbox
    inbox = await db.get_inbox(123)
    assert len(inbox) == 1
    assert inbox[0]["text"] == "Пересланное сообщение"
```

## Требования к тестированию

1. **Тесты forwarded сообщений:**
   - [ ] `test_forwarded_message_handling` — проверка обработки пересылок
   - [ ] `test_forwarded_message_in_inbox` — проверка сохранения в inbox
   - [ ] `test_forwarded_message_task_creation` — проверка создания задач

2. **Интеграционные тесты:**
   - [ ] Отправить пересланное сообщение через Telegram
   - [ ] Проверить, что оно появилось в inbox
   - [ ] Проверить саммаризацию с forwarded сообщениями

3. **Ручное тестирование:**
   - [ ] Переслать сообщение самому себе
   - [ ] Проверить `/inbox` команду
   - [ ] Проверить `/summarize` команду

## Обновление документации

После исправления обновить:
- `README.md` — секция "Обработка сообщений"
- `docs/architecture.md` — секция "Обработка пересылок"
- Документацию к `handlers/messages.py`

## Критерии приемки

- [ ] Forwarded сообщения корректно добавляются в inbox
- [ ] Задачи создаются из forwarded сообщений
- [ ] Саммаризация работает с forwarded сообщениями
- [ ] Все тесты проходят
- [ ] Логирование работает корректно

## Примеры кода для реализации

### Обработка forwarded в `handlers/messages.py`:
```python
@router.message(F.text)
async def handle_message(message: Message):
    """Обработка входящих сообщений."""
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем, это forwarded сообщение?
    is_forwarded = bool(message.forwarded)
    
    # Сохраняем в inbox
    await db.add_to_inbox(user_id, text, is_forwarded=is_forwarded)
    
    # Создаем задачу, если это вопрос
    if is_task_question(text):
        await db.add_task(user_id, text)
    
    # Отвечаем подтверждением
    await message.answer("✓ Сообщение получено")
```

### Обновление модели в `bot/db/models.py`:
```python
class InboxMessage(BaseModel):
    id: int
    user_id: int
    text: str
    timestamp: datetime
    is_forwarded: bool = False  # Новый атрибут
```

### Обновление БД в `bot/db/file_manager.py`:
```python
async def add_to_inbox(self, user_id: int, text: str, is_forwarded: bool = False):
    """Добавить сообщение в inbox."""
    message = {
        "id": len(self.inboxes[user_id]) + 1,
        "user_id": user_id,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "is_forwarded": is_forwarded  # Сохраняем флаг
    }
    self.inboxes[user_id].append(message)
    self._save_inboxes()
```

## Примечания

- Forwarded сообщения могут приходить из разных источников (личных чатов, групп, каналов)
- Важно сохранять метаданные forwarded (от кого, когда)
- Могут потребоваться дополнительные проверки на валидность forwarded данных