# Context Analyzer Module Documentation

## Overview

The ContextAnalyzer module handles intelligent grouping of related messages based on time and semantic similarity.

## Class: ContextAnalyzer

### Methods

#### `group_messages(messages: List[InboxMessage]) -> List[List[InboxMessage]]`

Main grouping function that combines time-based and semantic grouping.

**Steps:**
1. Sort messages by timestamp
2. Group by time window (30 minutes default)
3. Merge groups by semantic similarity

**Example:**
```python
analyzer = ContextAnalyzer()
groups = analyzer.group_messages(messages)
# Returns: [[msg1, msg2], [msg3], [msg4, msg5, msg6]]
```

#### `_group_by_time_window(messages, window_minutes=30)`

Groups consecutive messages within a time window.

**Logic:**
- Messages within 30 minutes of first message in group → same group
- Gap > 30 minutes → new group

**Example:**
```python
# Messages at: 10:00, 10:15, 10:45, 11:30
# Result: [[10:00, 10:15], [10:45], [11:30]]
```

#### `_group_by_similarity(groups)`

Merges adjacent groups based on semantic similarity.

**Criteria for merging:**
1. ≥ 3 common keywords (words > 3 chars)
2. Continuation patterns detected

**Continuation Patterns:**
- "как я говорил"
- "ещё по теме"
- "продолж"
- "связанн"
- "связано"
- "относ"

#### `detect_continuation(current, previous)`

Detects if a message continues a previous topic.

**Usage:**
```python
is_continuation = ContextAnalyzer.detect_continuation(msg1, msg2)
```

## Keywords Extraction

Simple tokenization:
- Lowercase conversion
- Words with length ≥ 3 characters
- Regex: `\b\w{3,}\b`

## Integration Flow

```
messages → group_messages()
    ↓
├─ _group_by_time_window() → time groups
└─ _group_by_similarity() → merged groups
    ↓
groups → OllamaClient.summarize_group()
```

## Example Usage

```python
from utils.context_analyzer import ContextAnalyzer
from bot.db.models import InboxMessage

analyzer = ContextAnalyzer()

# Get messages from inbox
messages = file_manager.read_messages(user_id)

# Group related messages
groups = analyzer.group_messages(messages)

# Each group can be summarized together
for group in groups:
    result = await ollama_client.summarize_group(group)
```