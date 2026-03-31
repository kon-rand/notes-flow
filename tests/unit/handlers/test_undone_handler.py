import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from pathlib import Path

from handlers.commands import undone_task_handler
from bot.db.models import Task


@pytest.fixture(autouse=True)
def cleanup_user_settings_and_files(tmp_path):
    """Clean up user settings and tmp_path before each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    if Path(SETTINGS_FILE).exists():
        Path(SETTINGS_FILE).unlink()
    yield
    # Clean up tmp_path after each test


@pytest.fixture
def mock_message():
    """Create a mock Telegram message"""
    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def unique_user_id():
    """Create unique user_id for each test to prevent cross-test interference"""
    import random
    return 5000000000 + random.randint(0, 1000000)


@pytest.mark.asyncio
async def test_undone_handler_active_task(mock_message, unique_user_id, tmp_path):
    """Test /undone_XXX with active task (not in archive)"""
    # Setup: Create active task
    from bot.db.file_manager import FileManager
    fm = FileManager(str(tmp_path))
    
    task = Task(
        id="task_001",
        title="Активная задача",
        tags=["актив"],
        status="completed",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Активная"
    )
    fm.append_task(unique_user_id, task)
    
    # Mock message with /undone_1
    mock_message.text = "/undone_1"
    mock_message.from_user.id = unique_user_id
    
    # Execute
    await undone_task_handler(mock_message)
    
    # Verify
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "не найдена" in call_args  # Task not in archive, restore_task_from_archive returns False


@pytest.mark.asyncio
async def test_undone_handler_archive_task(mock_message, unique_user_id, tmp_path):
    """Test /undone_XXX with archived task"""
    # Setup: Create archived task FIRST
    archive_dir = tmp_path / str(unique_user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    from bot.db.file_manager import FileManager
    fm = FileManager(str(tmp_path))
    
    # Mock message with /undone_1
    mock_message.text = "/undone_1"
    mock_message.from_user.id = unique_user_id
    
    # Create a custom file_manager for the handler
    import handlers.commands as commands
    original_file_manager = commands.FileManager
    
    def mock_file_manager_creator(*args, **kwargs):
        return FileManager(str(tmp_path))
    
    commands.FileManager = mock_file_manager_creator
    
    try:
        # Execute
        await undone_task_handler(mock_message)
        
        # Verify
        assert mock_message.answer.call_count >= 1
        calls = [str(call) for call in mock_message.answer.call_args_list]
        assert any("возвращена" in call for call in calls)
    finally:
        # Restore original
        commands.FileManager = original_file_manager
    
    # Verify task was moved to active
    tasks = fm.read_tasks(unique_user_id)
    assert len(tasks) == 1
    assert tasks[0].id == "task_001"
    assert tasks[0].status == "pending"
    assert tasks[0].archived_at is None


@pytest.mark.asyncio
async def test_undone_handler_task_not_found(mock_message, unique_user_id, tmp_path):
    """Test /undone_XXX with non-existent task"""
    # Setup: No tasks exist
    from bot.db.file_manager import FileManager
    fm = FileManager(str(tmp_path))
    
    # Mock message with /undone_999
    mock_message.text = "/undone_999"
    mock_message.from_user.id = unique_user_id
    
    # Execute
    await undone_task_handler(mock_message)
    
    # Verify
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "не найдена" in call_args


@pytest.mark.asyncio
async def test_undone_handler_invalid_format(mock_message):
    """Test /undone_XXX with invalid format (non-numeric)"""
    # Mock message with invalid format
    mock_message.text = "/undone_abc"
    mock_message.from_user.id = 123456789
    
    # Execute
    await undone_task_handler(mock_message)
    
    # Verify
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Неверный формат" in call_args


@pytest.mark.asyncio
async def test_undone_handler_from_user_none(mock_message):
    """Test /undone_XXX when from_user is None"""
    # Mock message with None from_user
    mock_message.from_user = None
    mock_message.text = "/undone_1"
    
    # Execute
    await undone_task_handler(mock_message)
    
    # Verify
    mock_message.answer.assert_not_called()
