# Utils Module Documentation

## Overview

The Utils module contains helper classes and functions for message analysis and AI integration.

## Components

### ContextAnalyzer (`context_analyzer.py`)

Analyzes and groups related messages based on time and semantic similarity.

**See:** [context_analyzer.md](context_analyzer.md)

### OllamaClient (`ollama_client.py`)

Handles communication with local Ollama LLM for message summarization.

#### Class: OllamaClient

**Initialization:**
```python
from utils.ollama_client import OllamaClient

client = OllamaClient()
# or with custom config
from utils.ollama_client import OllamaConfig
config = OllamaConfig(base_url="http://localhost:11434", model="llama3")
client = OllamaClient(config=config)
```

**Main Method:**

#### `summarize_group(messages: List[InboxMessage]) -> Dict[str, Any]`

Analyzes a group of messages and returns action decision.

**Parameters:**
- `messages` - List of inbox messages to analyze

**Returns:**
```python
{
    "action": "create_task" | "create_note" | "skip",
    "title": str,         # For create_task/create_note
    "tags": List[str],    # For create_task/create_note
    "content": str,       # For create_task/create_note
    "reason": str         # For skip
}
```

**Error Handling:**
- `Ollama not available` - Ollama server unreachable
- `Request timeout` - Request took too long
- `HTTP error` - Non-200 response
- `Parsing error` - Invalid JSON in response

**Internal Methods:**

##### `_format_messages(messages: List[InboxMessage]) -> str`

Formats messages for the prompt.

```python
"[2026-03-06T14:30:00] User 123456:\nHello world\n\n"
```

##### `_build_prompt(messages_text: str) -> str`

Builds the prompt for the LLM.

Uses task-focused prompt asking for:
- Clear task title
- Up to 3 tags
- Full description in content

##### `_parse_response(response_text: str) -> Dict[str, Any]`

Parses JSON from LLM response.

Extracts JSON object from text using `{` and `}` positions.

#### Integration Flow

```
messages → summarize_group()
    ↓
_format_messages() → formatted text
    ↓
_build_prompt() → prompt
    ↓
POST /api/generate → LLM response
    ↓
_parse_response() → decision dict
```

### Markdown Parser (`markdown_parser.py`)

Parses YAML frontmatter and markdown content.

**See:** [db.md](db.md) for file format details.

## Module Dependencies

- `httpx` - Async HTTP client
- `bot.config` - Settings
- `bot.db.models` - Data models

## Usage Example

```python
from utils.ollama_client import OllamaClient
from bot.db.models import InboxMessage

client = OllamaClient()

messages = [...]  # List of InboxMessage
result = await client.summarize_group(messages)

if result["action"] == "create_task":
    # Create task
    pass
elif result["action"] == "create_note":
    # Create note
    pass
else:
    # Skip
    pass
```