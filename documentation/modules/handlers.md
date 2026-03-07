# Handlers Module Documentation

## Overview

Handlers module contains all Telegram bot event handlers for messages and commands.

## Files

### `commands.py`

Bot command implementations.

**Commands:**

| Command | Description | Handler Function |
|---------|-------------|------------------|
| `/start` | Welcome message with stats | `start_handler` |
| `/summarize` | Manual summarization trigger | `summarize_handler` |
| `/inbox` | View current inbox messages | `inbox_handler` |
| `/tasks` | List all tasks | `tasks_handler` |
| `/notes` | List all notes | `notes_handler` |
| `/settings delay <minutes>` | Set summarization delay | `settings_handler` |
| `/clear inbox` | Clear inbox manually | `clear_handler` |

**Example:**
```python
@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    stats = get_user_stats(message.from_user.id)
    await message.answer(f"👋 Привет! Статистика: {stats}")
```

### `messages.py`

Incoming message processing.

**Main Handler:** `message_handler`

**Flow:**
1. Extract `user_id` from `message.from_user.id`
2. Check for forwarded messages (`message.forward_origin`)
3. Parse forward author information
4. Create `InboxMessage` object
5. Save to `FileManager.append_message()`
6. Trigger `SummarizeTimer.schedule_summarization()`

**Forward Message Handling:**
```python
if message.forward_origin:
    if isinstance(message.forward_origin, MessageOriginUser):
        forward_author_id = message.forward_origin.sender_id
        forward_author_name = message.forward_origin.sender_name
```

### `summarizer.py`

Auto-summarization logic.

**Main Function:** `auto_summarize(user_id, bot)`

**Steps:**
1. Read all inbox messages for user
2. Group messages using `ContextAnalyzer.group_messages()`
3. For each group:
   - Call `OllamaClient.summarize_group()`
   - Create task or note based on response
4. Clear inbox after processing
5. Send summary report to user

**Response Format:**
```python
{
    "tasks_created": 2,
    "notes_created": 1,
    "skipped": 3,
    "report": ["✅ Создана задача: ...", "📝 Создана заметка: ..."]
}
```

## Module Dependencies

- `aiogram` - Message/Command types
- `bot.db.file_manager` - Data access
- `bot.db.models` - Data models
- `utils.context_analyzer` - Message grouping
- `utils.ollama_client` - AI processing

## Integration

```
Telegram Updates → Dispatcher
    ↓
├─ Commands → commands.py
├─ Messages → messages.py → SummarizeTimer
└─ Manual Summarize → summarizer.py
```