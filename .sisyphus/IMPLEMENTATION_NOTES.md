# Dynamic /tasks Message Updates - Implementation Notes

## Overview
Implemented dynamic message updates for `/tasks` and `/archive` commands. Instead of sending new messages each time, the bot now edits existing messages when tasks change.

## Changes Made

### 1. Database Model (`bot/db/models.py`)
- Added `tasks_message_id: Optional[int] = None` to UserSettings
- Added `archive_message_id: Optional[int] = None` to UserSettings

### 2. User Settings (`bot/config/user_settings.py`)
- Added `_save()` method to include `tasks_message_id` and `archive_message_id` in JSON
- Added `update_tasks_message_id(user_id, new_id)` method
- Added `update_archive_message_id(user_id, new_id)` method

### 3. Helper Functions (`bot/helpers/message_updater.py`)
Created two helper functions:
- `update_or_create_task_message(message, text)` - Updates/creates /tasks message
- `update_or_create_archive_message(message, text)` - Updates/creates /archive message

Logic:
- If `message_id` exists and is valid → use `bot.edit_message_text()`
- If `message_id` is None or edit fails → send new message with `message.answer()`
- Gracefully handles edge cases (message too old, deleted, etc.)
- **FIXED**: Now uses `update_tasks_message_id()` and `update_archive_message_id()` instead of `update_last_message_id()`

### 4. Command Handlers (`handlers/commands.py`)
Modified the following handlers to use helper functions:
- `tasks_handler` - uses `update_or_create_task_message`
- `archive_handler` - uses `update_or_create_archive_message`
- `notes_handler` - uses `update_or_create_archive_message`
- `inbox_handler` - uses `update_or_create_archive_message`
- `clear_handler` - uses both helpers after clearing inbox
- `done_task_handler` - uses `update_or_create_task_message` after task completion
- `undone_task_handler` - uses `update_or_create_task_message` after task restoration
- `delete_task_handler` - uses `update_or_create_task_message` after task deletion

### 5. Summarizer Integration (`handlers/summarizer.py`)
- Added import for `update_or_create_task_message`
- After successful summarization, calls `update_or_create_task_message` to update /tasks

## Edge Cases Handled
1. **First run**: No stored message_id → sends new message and saves ID
2. **Message too old (>48h)**: Edit fails → sends new message
3. **Message deleted**: Edit fails → sends new message
4. **Bot errors**: Catches exceptions and falls back to sending new message without saving ID

## Bug Fix (Critical)
**Issue**: Message ID was being saved to `last_message_id` field instead of `tasks_message_id`/`archive_message_id`
**Fix**: Added separate methods `update_tasks_message_id()` and `update_archive_message_id()` and updated helper functions to use them

## Testing
- All 343 unit tests pass
- Edge case tests added in `tests/unit/helpers/test_message_updater.py`
- Integration tests updated to mock helper functions

## Verification
To verify the implementation:
1. Run `/tasks` - should send initial message
2. Run `/done_123` - should edit the existing /tasks message (not send new one)
3. Run `/tasks` again - should still show the same message (edited)
4. Run `/archive` - should send/edit archive message
5. Run `/summarize` - should update /tasks after summarization

## Files Modified
- `bot/db/models.py`
- `bot/config/user_settings.py`
- `bot/helpers/message_updater.py` (new)
- `bot/helpers/__init__.py` (new)
- `handlers/commands.py`
- `handlers/summarizer.py`
- `tests/unit/helpers/test_message_updater.py` (new)
- `tests/unit/handlers/test_commands.py`
- `tests/unit/handlers/test_undone_handler.py`
- `tests/integration/test_commands_archive.py`
