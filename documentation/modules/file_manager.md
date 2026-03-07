# File Manager Module Documentation

## Overview

FileManager handles all file-based data storage operations using Markdown files with YAML frontmatter.

## Class: FileManager

### Initialization

```python
file_manager = FileManager(data_dir="data")
```

**Parameters:**
- `data_dir` (str) - Base directory for user data (default: "data")

### Directory Structure

```
data/
├── {user_id}/
│   ├── inbox.md
│   ├── tasks.md
│   └── notes.md
```

## Methods

### Message Operations

#### `append_message(user_id, message: InboxMessage)`

Add message to user's inbox.

**Example:**
```python
msg = InboxMessage(
    id="msg_001",
    timestamp=datetime.now(),
    from_user=123456,
    sender_id=123456,
    sender_name=None,
    content="Hello",
    chat_id=-100123456
)
file_manager.append_message(123456, msg)
```

#### `read_messages(user_id) -> List[InboxMessage]`

Read all inbox messages for user.

**Returns:** List of `InboxMessage` objects

#### `clear_messages(user_id)`

Delete all messages from inbox.

### Task Operations

#### `append_task(user_id, task: Task)`

Add task to user's tasks file.

**Example:**
```python
task = Task(
    id="task_001",
    title="Do something",
    tags=["work", "urgent"],
    status="pending",
    created_at=datetime.now(),
    source_message_ids=["msg_001", "msg_002"],
    content="Do it by tomorrow"
)
file_manager.append_task(123456, task)
```

#### `read_tasks(user_id) -> List[Task]`

Read all tasks for user.

#### `update_task_status(user_id, task_id, status)`

Update task status (pending/completed).

**Returns:** `True` if updated, `False` if not found

### Note Operations

#### `append_note(user_id, note: Note)`

Add note to user's notes file.

**Example:**
```python
note = Note(
    id="note_001",
    title="Ideas",
    tags=["ideas"],
    created_at=datetime.now(),
    source_message_ids=["msg_003"],
    content="Use async/await"
)
file_manager.append_note(123456, note)
```

#### `read_notes(user_id) -> List[Note]`

Read all notes for user.

## File Format

### YAML Frontmatter
```yaml
---
type: inbox
---
```

### Item Format
```markdown
## msg_001
timestamp: 2026-03-06T14:30:00
from_user: 123456
sender_id: 123456
sender_name: null
content: Message content
chat_id: -100123456
```

### Multiple Items
```yaml
---
type: task
---

## task_001
title: Task 1
tags: [work, urgent]
status: pending
created_at: 2026-03-06T14:30:00
source_message_ids: [msg_001, msg_002]
content: Task description
```

## Internal Methods

### `_get_user_dir(user_id) -> Path`

Get or create user directory.

### `_generate_id(prefix, existing_ids) -> str`

Generate unique ID (e.g., "msg_001", "task_002").

### `_read_file(file_path) -> Optional[dict]`

Parse Markdown file with YAML frontmatter.

### `_parse_file(content) -> dict`

Extract metadata and items from file content.

### `_serialize_item(item_data) -> str`

Convert item dict to Markdown format.

### `_write_file(file_path, file_type, items)`

Write file with YAML frontmatter and items.

### `_load_all_items(user_id, file_type) -> List[tuple]`

Load all items from file as (id, data) tuples.