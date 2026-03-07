# Bot Module Documentation

## Overview

The bot module contains the core Telegram bot implementation using aiogram 3.x framework.

## Files

### `config.py`

Configuration management using Pydantic Settings.

**Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot API token (required)
- `OLLAMA_BASE_URL` - Ollama API URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL` - LLM model name (default: `llama3`)
- `DEFAULT_SUMMARIZE_DELAY` - Default delay in seconds (default: `300`)

**Usage:**
```python
from bot.config import settings

print(settings.TELEGRAM_BOT_TOKEN)
print(settings.OLLAMA_BASE_URL)
```

### `main.py`

Bot entry point and aiogram dispatcher setup.

**Key Components:**
- Bot initialization with aiogram `Bot` class
- Dispatcher setup with event handlers
- Webhook or polling configuration
- Startup/shutdown event handlers

### `timers/manager.py`

`SummarizeTimer` class for managing delayed summarization.

**Methods:**
- `schedule_summarization(user_id, delay_seconds)` - Schedule auto-summarization
- `reset(user_id)` - Cancel previous timer and start new one
- `_wait_and_summarize(user_id, delay)` - Async timer implementation

**Behavior:**
- Each new message resets the timer
- Prevents duplicate summarization
- Uses asyncio for non-blocking delays

## Module Dependencies

- `aiogram` - Telegram bot framework
- `bot.config` - Settings
- `bot.db.file_manager` - Data storage
- `handlers.summarizer` - Auto-summarization logic

## Integration Flow

```
User Message → handlers/messages.py → SummarizeTimer.schedule()
                                    ↓
                              (after delay)
                                    ↓
                              handlers.summarizer.auto_summarize()
```