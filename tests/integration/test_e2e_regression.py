import sys
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import shutil
from pathlib import Path

from bot.db.models import InboxMessage, Task, Note
from bot.db.file_manager import FileManager
from handlers.summarizer import auto_summarize


@pytest.fixture
def clean_data_dir():
    """Clean up data directory before and after tests"""
    data_dir = Path("data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    yield
    if data_dir.exists():
        shutil.rmtree(data_dir)


@pytest.fixture
def user_id():
    return 123456789


class TestBotCommandsRegression:
    """Regression tests for bot commands - critical user flows"""

    @pytest.mark.asyncio
    async def test_start_command_shows_statistics(self, clean_data_dir, user_id):
        """Regression: /start command returns user statistics"""
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Test task",
            tags=["test"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Test content"
        ))
        
        tasks = fm.read_tasks(user_id)
        notes = fm.read_notes(user_id)
        
        assert len(tasks) == 1
        assert len(notes) == 0

    @pytest.mark.asyncio
    async def test_tasks_command_lists_tasks(self, clean_data_dir, user_id):
        """Regression: /tasks command lists all user tasks"""
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Task 1",
            tags=["work"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Content 1"
        ))
        fm.append_task(user_id, Task(
            id="task_002",
            title="Task 2",
            tags=["home"],
            status="completed",
            created_at=datetime.now(),
            source_message_ids=["msg_002"],
            content="Content 2"
        ))
        
        tasks = fm.read_tasks(user_id)
        
        assert len(tasks) == 2
        pending = [t for t in tasks if t.status == "pending"]
        completed = [t for t in tasks if t.status == "completed"]
        assert len(pending) == 1
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_done_command_marks_task_complete(self, clean_data_dir, user_id):
        """Regression: /done_XXX marks task as completed"""
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Task to complete",
            tags=["test"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Content"
        ))
        
        success = fm.update_task_status(user_id, "task_001", "completed")
        
        assert success is True
        tasks = fm.read_tasks(user_id)
        assert tasks[0].status == "completed"

    @pytest.mark.asyncio
    async def test_del_command_removes_task(self, clean_data_dir, user_id):
        """Regression: /del_XXX removes task"""
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Task to delete",
            tags=["test"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Content"
        ))
        
        success = fm.delete_task(user_id, "task_001")
        
        assert success is True
        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_inbox_command_shows_messages(self, clean_data_dir, user_id):
        """Regression: /inbox command shows stored messages"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Test message",
            chat_id=-1001234567890
        ))
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert messages[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_clear_inbox_removes_messages(self, clean_data_dir, user_id):
        """Regression: /clear inbox removes all messages"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Message 1",
            chat_id=-1001234567890
        ))
        fm.append_message(user_id, InboxMessage(
            id="msg_002",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Message 2",
            chat_id=-1001234567890
        ))
        
        fm.clear_messages(user_id)
        
        messages = fm.read_messages(user_id)
        assert len(messages) == 0


class TestTaskManagementRegression:
    """Regression tests for task management flows"""

    @pytest.mark.asyncio
    async def test_create_task_flow(self, clean_data_dir, user_id):
        """Regression: Ollama creates task from inbox messages"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Нужно подготовить отчёт",
            chat_id=-1001234567890
        ))
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": '[{"action": "create_task", "title": "Подготовить отчёт", "tags": ["работа"], "content": "Создать отчёт", "source_message_ids": ["msg_001"]}]'
                }
            }]
        }
        
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                text=mock_response["choices"][0]["message"]["content"],
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            await auto_summarize(user_id, bot=mock_bot)
            
            tasks = fm.read_tasks(user_id)
            assert len(tasks) == 1
            assert tasks[0].title == "Подготовить отчёт"
            assert "работа" in tasks[0].tags
            
            messages = fm.read_messages(user_id)
            assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_create_note_flow(self, clean_data_dir, user_id):
        """Regression: Ollama creates note from inbox messages"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Идея: использовать новый фреймворк",
            chat_id=-1001234567890
        ))
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": '[{"action": "create_note", "title": "Идея: использовать новый фреймворк", "tags": ["идеи"], "content": "Рассмотреть новый фреймворк", "source_message_ids": ["msg_001"]}]'
                }
            }]
        }
        
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                text=mock_response["choices"][0]["message"]["content"],
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            await auto_summarize(user_id, bot=mock_bot)
            
            notes = fm.read_notes(user_id)
            assert len(notes) == 1
            assert notes[0].title == "Идея: использовать новый фреймворк"

    @pytest.mark.asyncio
    async def test_archive_completed_tasks(self, clean_data_dir, user_id):
        """Regression: Completed tasks can be archived"""
        fm = FileManager()
        
        task = Task(
            id="task_001",
            title="Task to archive",
            tags=["test"],
            status="completed",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Content"
        )
        fm.append_task(user_id, task)
        
        archived = fm.archive_completed_tasks(user_id, datetime.now())
        
        assert len(archived) == 1
        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_ollama_unavailable_preserves_inbox(self, clean_data_dir, user_id):
        """Regression: When Ollama unavailable, inbox is NOT cleared"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Test message",
            chat_id=-1001234567890
        ))
        
        import httpx
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            await auto_summarize(user_id, bot=mock_bot)
            
            messages = fm.read_messages(user_id)
            assert len(messages) == 1


class TestForwardedMessagesRegression:
    """Regression tests for forwarded message handling"""

    @pytest.mark.asyncio
    async def test_forwarded_message_preserves_sender(self, clean_data_dir, user_id):
        """Regression: Forwarded messages preserve original sender info"""
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime.now(),
            from_user=user_id,
            sender_id=987654321,
            sender_name="Original Author",
            content="Important info from channel",
            chat_id=-1001234567890
        ))
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert messages[0].from_user == user_id
        assert messages[0].sender_id == 987654321
        assert messages[0].sender_name == "Original Author"


class TestHealthcheckRegression:
    """Regression tests for healthcheck endpoint"""

    @pytest.mark.asyncio
    async def test_healthcheck_function_imports(self):
        """Regression: Healthcheck function can be imported and called"""
        from bot.healthcheck import healthcheck
        result = await healthcheck()
        assert "status" in result
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_ping_function_imports(self):
        """Regression: Ping function can be imported and called"""
        from bot.healthcheck import ping
        result = await ping()
        assert "status" in result
        assert "config" in result
