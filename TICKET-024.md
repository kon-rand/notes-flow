# TICKET-024: Добавить уведомления о начале и результате саммаризации

## Описание
Бот автоматически саммаризирует сообщения после задержки, но не уведомляет пользователя о процессе. Необходимо добавить уведомления о начале и результате саммаризации.

## Компоненты
- Модифицировать `bot/timers/manager.py` - добавить start notification
- Модифицировать `handlers/summarizer.py` - улучшить result notification
- Модифицировать `handlers/messages.py` - передавать user_name и bot в таймер
- Написать unit-тесты для уведомлений
- Обновить README.md с документацией

## Приоритет
🟡 средний

## Статус
🚧 in_progress

---

## Реализация

### 1. Start Notification (уведомление о начале)

**Файл**: `bot/timers/manager.py`

**Функция**: `_wait_and_summarize`

**Формат сообщения**:
```
🔄 Саммаризация сообщений началась для пользователя {user_name or user_id}
```

**Реализация**:
```python
async def _wait_and_summarize(
    self, user_id: int, delay: int, user_name: Optional[str] = None, bot: Optional[Bot] = None
) -> None:
    """Асинхронный таймер с задержкой"""
    # Отправка уведомления о начале ПЕРЕД ожиданием
    if bot:
        display_name = user_name or str(user_id)
        try:
            await bot.send_message(
                user_id,
                f"🔄 Саммаризация сообщений началась для пользователя {display_name}"
            )
        except Exception:
            pass  # Игнорируем ошибки отправки
    
    await asyncio.sleep(delay)
    
    from handlers.summarizer import auto_summarize
    await auto_summarize(user_id, bot=bot)
```

**Изменения в `schedule_summarization`**:
```python
async def schedule_summarization(
    self, 
    user_id: int, 
    delay_seconds: Optional[int] = None, 
    user_name: Optional[str] = None,
    bot: Optional[Bot] = None
) -> None:
    """Запланировать саммаризацию с задержкой"""
    if delay_seconds is None:
        delay_seconds = settings.DEFAULT_SUMMARIZE_DELAY
    
    # Cancel previous timer
    if user_id in self.timers:
        self.timers[user_id].cancel()
    
    # Schedule new timer
    task = asyncio.create_task(
        self._wait_and_summarize(user_id, delay_seconds, user_name, bot)
    )
    self.timers[user_id] = task
```

### 2. Enhanced Result Notification (улучшенное уведомление о результате)

**Файл**: `handlers/summarizer.py`

**Функция**: `auto_summarize`

**Формат сообщения**:
```
✅ Саммаризация завершена

Создано:
- Задач: {count_tasks}
- Заметок: {count_notes}

Созданные задачи:
• {title} (tags: {tag1}, {tag2})
• {title} (tags: {tag1})

Созданные заметки:
• {title}
• {title}

Показать все: используйте /tasks и /notes

Используйте /tasks для просмотра задач, /notes для просмотра заметок
```

**Реализация**:
```python
async def auto_summarize(user_id: int, bot: Optional[Bot] = None) -> None:
    """Автоматическая саммаризация сообщений пользователя"""
    try:
        # Read messages
        messages = file_manager.read_messages(user_id)
        
        if not messages:
            return
        
        # Call LLM
        results = await ollama_client.summarize_messages(messages)
        
        # Track created items
        created_tasks = []
        created_notes = []
        
        # Process results
        for result in results:
            if result.get("action") == "create_task":
                task = Task(
                    id=f"task_{generate_id()}",
                    title=result["title"],
                    tags=result.get("tags", []),
                    status="pending",
                    created_at=datetime.now(),
                    source_message_ids=[msg.id for msg in messages],
                    content=result["content"]
                )
                file_manager.append_task(user_id, task)
                created_tasks.append(task)
            
            elif result.get("action") == "create_note":
                note = Note(
                    id=f"note_{generate_id()}",
                    title=result["title"],
                    tags=result.get("tags", []),
                    created_at=datetime.now(),
                    source_message_ids=[msg.id for msg in messages],
                    content=result["content"]
                )
                file_manager.append_note(user_id, note)
                created_notes.append(note)
        
        # Clear inbox
        file_manager.clear_messages(user_id)
        
        # Send enhanced notification
        if bot:
            report_lines = [
                "✅ Саммаризация завершена",
                "",
                "Создано:",
                f"- Задач: {len(created_tasks)}",
                f"- Заметок: {len(created_notes)}",
                ""
            ]
            
            # Add tasks (first 10 total)
            if created_tasks:
                report_lines.append("Созданные задачи:")
                for i, task in enumerate(created_tasks[:10]):
                    tags_str = ", ".join(task.tags) if task.tags else "нет тегов"
                    report_lines.append(f"• {task.title} (tags: {tags_str})")
            
            # Add notes (first 10 total)
            if created_notes:
                report_lines.append("Созданные заметки:")
                for i, note in enumerate(created_notes[:10]):
                    report_lines.append(f"• {note.title}")
            
            # Add pagination hint if more than 10
            total_items = len(created_tasks) + len(created_notes)
            if total_items > 10:
                report_lines.append("")
                report_lines.append("Показать все: используйте /tasks и /notes")
            
            # Add footer
            report_lines.append("")
            report_lines.append("Используйте /tasks для просмотра задач, /notes для просмотра заметок")
            
            report_text = "\n".join(report_lines)
            
            try:
                await bot.send_message(user_id, report_text.strip())
            except Exception:
                pass  # Игнорируем ошибки отправки
        
    except Exception as e:
        logger.error(f"Error in auto_summarize for user {user_id}: {e}")
        if bot:
            try:
                await bot.send_message(
                    user_id,
                    "❌ Ошибка при саммаризации. Попробуйте /summarize позже."
                )
            except Exception:
                pass
```

### 3. Update `handlers/messages.py` to pass user_name and bot

**Файл**: `handlers/messages.py`

**Изменения**:
```python
@dp.message_handler(content_types=["text", "forwarded"])
async def message_handler(message: Message) -> None:
    """Обработка входящих сообщений"""
    user_id = message.from_user.id if message.from_user else None
    
    # Extract forward info if present
    forward_info = extract_forward_info(message)
    
    # Create inbox message
    inbox_message = InboxMessage(
        id=f"msg_{generate_id()}",
        timestamp=datetime.now(),
        from_user=user_id,
        sender_id=forward_info.sender_id if forward_info else user_id,
        sender_name=forward_info.sender_name,
        content=message.text or (message.caption if message.caption else ""),
        chat_id=message.chat.id
    )
    
    # Save to inbox
    file_manager.append_message(user_id, inbox_message)
    
    # Schedule summarization with user_name and bot
    user_name = message.from_user.full_name if message.from_user else None
    await summarizer_timer.schedule_summarization(
        user_id=user_id,
        user_name=user_name,
        bot=message.bot
    )
```

---

## Тестирование

### Unit Tests for Start Notification

**Файл**: `tests/unit/bot/timers/test_summarize_timer.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.timers.manager import SummarizeTimer
from aiogram import Bot


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def timer():
    return SummarizeTimer()


@pytest.mark.asyncio
async def test_schedule_summarization_with_user_name(timer, mock_bot):
    """Test that user_name is passed through to _wait_and_summarize"""
    with patch('asyncio.sleep', new_callable=AsyncMock):
        await timer.schedule_summarization(
            user_id=123,
            delay_seconds=60,
            user_name="Test User",
            bot=mock_bot
        )
        
        # Give task time to execute
        await asyncio.sleep(0.1)
        
        # Verify start notification was sent
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[0][1] == "🔄 Саммаризация сообщений началась для пользователя Test User"


@pytest.mark.asyncio
async def test_wait_and_summarize_handles_missing_user_name(timer, mock_bot):
    """Test that user_id is used when user_name is unavailable"""
    with patch('asyncio.sleep', new_callable=AsyncMock):
        await timer.schedule_summarization(
            user_id=123,
            delay_seconds=60,
            user_name=None,
            bot=mock_bot
        )
        
        await asyncio.sleep(0.1)
        
        # Verify notification was sent with user_id
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert "123" in call_args[0][1]


@pytest.mark.asyncio
async def test_wait_and_summarize_sends_start_notification_before_delay(timer, mock_bot):
    """Test that start notification is sent before delay"""
    call_order = []
    
    async def mock_sleep(seconds):
        call_order.append("sleep")
        await asyncio.sleep(0.01)
    
    async def mock_wait_and_summarize():
        call_order.append("start_notification")
        await mock_sleep(60)
    
    with patch('asyncio.sleep', mock_sleep):
        await timer.schedule_summarization(
            user_id=123,
            delay_seconds=60,
            user_name="Test",
            bot=mock_bot
        )
        
        await asyncio.sleep(0.1)
        
        # Verify notification was sent
        assert mock_bot.send_message.called
```

### Unit Tests for Enhanced Result Notification

**Файл**: `tests/unit/handlers/test_summarizer.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.summarizer import auto_summarize
from bot.db.models import Task, Note
from aiogram import Bot


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_auto_summarize_sends_enhanced_result_notification(mock_bot):
    """Test that enhanced notification is sent with detailed format"""
    with patch('handlers.summarizer.file_manager') as mock_fm, \
         patch('handlers.summarizer.ollama_client') as mock_ollama:
        
        # Setup mock messages
        mock_messages = [
            MagicMock(id="msg_001", content="Test message"),
            MagicMock(id="msg_002", content="Another message")
        ]
        mock_fm.read_messages.return_value = mock_messages
        
        # Setup mock LLM results
        mock_ollama.summarize_messages = AsyncMock(return_value=[
            {
                "action": "create_task",
                "title": "Test Task",
                "tags": ["tag1", "tag2"],
                "content": "Test content"
            }
        ])
        
        await auto_summarize(user_id=123, bot=mock_bot)
        
        # Verify notification was sent
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[0][1]
        
        # Verify format
        assert "✅ Саммаризация завершена" in call_args
        assert "Создано:" in call_args
        assert "Задач: 1" in call_args
        assert "Созданные задачи:" in call_args
        assert "• Test Task (tags: tag1, tag2)" in call_args


@pytest.mark.asyncio
async def test_auto_summarize_notification_limits_to_10_items(mock_bot):
    """Test that notification limits to first 10 items"""
    with patch('handlers.summarizer.file_manager') as mock_fm, \
         patch('handlers.summarizer.ollama_client') as mock_ollama:
        
        mock_messages = [MagicMock(id="msg_001", content="Test")]
        mock_fm.read_messages.return_value = mock_messages
        
        # Create 15 tasks
        mock_results = [
            {
                "action": "create_task",
                "title": f"Task {i}",
                "tags": ["tag"],
                "content": "Content"
            }
            for i in range(15)
        ]
        mock_ollama.summarize_messages = AsyncMock(return_value=mock_results)
        
        await auto_summarize(user_id=123, bot=mock_bot)
        
        call_args = mock_bot.send_message.call_args[0][1]
        
        # Verify only 10 items shown
        assert call_args.count("• Task") == 10
        assert "Показать все: используйте /tasks и /notes" in call_args


@pytest.mark.asyncio
async def test_auto_summarize_notification_format_with_tags(mock_bot):
    """Test that task format includes tags correctly"""
    with patch('handlers.summarizer.file_manager') as mock_fm, \
         patch('handlers.summarizer.ollama_client') as mock_ollama:
        
        mock_messages = [MagicMock(id="msg_001", content="Test")]
        mock_fm.read_messages.return_value = mock_messages
        
        mock_ollama.summarize_messages = AsyncMock(return_value=[
            {
                "action": "create_task",
                "title": "Task with no tags",
                "tags": [],
                "content": "Content"
            }
        ])
        
        await auto_summarize(user_id=123, bot=mock_bot)
        
        call_args = mock_bot.send_message.call_args[0][1]
        assert "• Task with no tags (tags: нет тегов)" in call_args


@pytest.mark.asyncio
async def test_auto_summarize_notification_format_notes(mock_bot):
    """Test that note format is correct"""
    with patch('handlers.summarizer.file_manager') as mock_fm, \
         patch('handlers.summarizer.ollama_client') as mock_ollama:
        
        mock_messages = [MagicMock(id="msg_001", content="Test")]
        mock_fm.read_messages.return_value = mock_messages
        
        mock_ollama.summarize_messages = AsyncMock(return_value=[
            {
                "action": "create_note",
                "title": "Test Note",
                "tags": ["note"],
                "content": "Content"
            }
        ])
        
        await auto_summarize(user_id=123, bot=mock_bot)
        
        call_args = mock_bot.send_message.call_args[0][1]
        assert "Созданные заметки:" in call_args
        assert "• Test Note" in call_args
```

---

## Обновление документации

### README.md

**Раздел "Использование" - добавить**:

```markdown
### Уведомления о саммаризации

Бот автоматически уведомляет о процессе саммаризации:

1. **Начало**: При запуске таймера отправляется уведомление
   ```
   🔄 Саммаризация сообщений началась для пользователя {имя}
   ```

2. **Результат**: После завершения отправляется детальный отчёт
   ```
   ✅ Саммаризация завершена

   Создано:
   - Задач: 2
   - Заметок: 1

   Созданные задачи:
   • Купить молоко (tags: покупки)
   • Позвонить маме (tags: семья)

   Созданные заметки:
   • Идеи для проекта

   Используйте /tasks для просмотра задач, /notes для просмотра заметок
   ```

**Раздел "Функции" - добавить**:

```markdown
### Управление
- ✅ Ручной запуск саммаризации по команде
- ✅ Просмотр инбокса, задач и заметок
- ✅ Настройка задержки саммаризации
- ✅ Очистка инбокса вручную
- ✅ Уведомления о начале и результате саммаризации
```

---

## Технические детали

### Архитектурные изменения

1. **SummarizeTimer**: Теперь принимает `user_name` и `bot` параметры
2. **auto_summarize**: Теперь принимает `bot` параметр для отправки уведомлений
3. **message_handler**: Передаёт `user_name` и `bot` в таймер

### Поток обработки

```
User sends message
    ↓
message_handler (handlers/messages.py)
    ↓
Extract user_name = message.from_user.full_name
    ↓
summarizer_timer.schedule_summarization(user_id, user_name, bot)
    ↓
_wait_and_summarize(user_id, delay, user_name, bot)
    ↓
Send start notification: "🔄 Саммаризация..."
    ↓
asyncio.sleep(delay)
    ↓
auto_summarize(user_id, bot)
    ↓
Process LLM results, create tasks/notes
    ↓
Send result notification with detailed format
```

### Обработка ошибок

- Ошибки отправки уведомлений игнорируются (try/except)
- Если саммаризация не удалась, отправляется ошибка
- Если user_name недоступен, используется user_id

---

## Критерии успеха

- [x] Start notification sent when timer begins
- [x] Result notification shows detailed format
- [x] Tasks displayed with tags
- [x] Notes displayed with titles
- [x] Pagination for >10 items
- [x] All tests passing
- [x] Documentation updated
- [x] No regressions in existing functionality

---

**План составлен**: 2026-03-25
**Версия**: 1.0