# Summarizer Module Documentation

## Overview

The Summarizer module handles automatic processing and conversion of message groups into tasks and notes using AI.

## Function: `auto_summarize(user_id, bot)`

Main async function for automatic summarization.

### Parameters

- `user_id` (int) - Telegram user ID
- `bot` (Optional[Bot]) - Telegram bot instance for sending messages

### Return Value

```python
{
    "tasks_created": int,
    "notes_created": int,
    "skipped": int,
    "report": List[str]
}
```

Or on error:
```python
{"error": str}
```

### Processing Flow

1. **Read Messages**
   ```python
   messages = file_manager.read_messages(user_id)
   ```

2. **Group Messages**
   ```python
   analyzer = ContextAnalyzer()
   groups = analyzer.group_messages(messages)
   ```

3. **Process Each Group**
   ```python
   for group in groups:
       result = await client.summarize_group(group)
       
       if result["action"] == "create_task":
           # Create task
       elif result["action"] == "create_note":
           # Create note
       else:
           # Skip
   ```

4. **Clear Inbox**
   ```python
   file_manager.clear_messages(user_id)
   ```

5. **Send Report**
   ```python
   report_text = f"""♻️ Саммаризация завершена:
   
   ✅ Задачи создано: {tasks_created}
   📝 Заметок создано: {notes_created}
   ⏭ Пропущено: {skipped}
   """
   ```

### Ollama Response Handling

**Task Creation:**
```python
result = {
    "action": "create_task",
    "title": "Задача",
    "tags": ["tag1", "tag2"],
    "content": "Описание"
}
```

**Note Creation:**
```python
result = {
    "action": "create_note",
    "title": "Заметка",
    "tags": ["idea"],
    "content": "Информация"
}
```

**Skip:**
```python
result = {"action": "skip", "reason": "Not important"}
```

### Error Handling

- Ollama unavailable → skip group
- Timeout → skip group
- Parse error → skip group
- Send error message to user

## Integration

```
SummarizeTimer timeout → auto_summarize()
    ↓
ContextAnalyzer.group_messages()
    ↓
OllamaClient.summarize_group()
    ↓
FileManager.append_task/note()
    ↓
FileManager.clear_messages()
    ↓
Send report to user
```