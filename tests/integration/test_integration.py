import sys
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import shutil
from pathlib import Path

from bot.db.models import InboxMessage, Task, Note
from bot.db.file_manager import FileManager
from utils.ollama_client import OllamaClient
from utils.context_analyzer import ContextAnalyzer
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
def sample_message():
    """Create a sample inbox message"""
    return InboxMessage(
        id="msg_001",
        timestamp=datetime(2026, 3, 6, 14, 0, 0),
        from_user=123456789,
        sender_id=123456789,
        sender_name="Test User",
        content="Нужно подготовить отчёт по проекту",
        chat_id=-1001234567890
    )


@pytest.fixture
def sample_messages():
    """Create multiple sample messages"""
    return [
        InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=123456789,
            sender_id=123456789,
            sender_name="Test User",
            content="Нужно подготовить отчёт по проекту",
            chat_id=-1001234567890
        ),
        InboxMessage(
            id="msg_002",
            timestamp=datetime(2026, 3, 6, 14, 5, 0),
            from_user=123456789,
            sender_id=123456789,
            sender_name="Test User",
            content="Вот данные для отчёта: [ссылка на файл]",
            chat_id=-1001234567890
        ),
    ]


class TestFileManagerIntegration:
    """Integration tests for FileManager"""

    def test_append_and_read_message(self, clean_data_dir, sample_message):
        """Test: append message → read messages"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_message(user_id, sample_message)
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert messages[0].id == "msg_001"
        assert messages[0].content == "Нужно подготовить отчёт по проекту"
        assert messages[0].from_user == user_id

    def test_clear_messages(self, clean_data_dir, sample_message):
        """Test: append messages → clear → verify empty"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_message(user_id, sample_message)
        fm.clear_messages(user_id)
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 0

    def test_multiple_messages(self, clean_data_dir, sample_messages):
        """Test: append multiple messages → read all"""
        user_id = 123456789
        fm = FileManager()
        
        for msg in sample_messages:
            fm.append_message(user_id, msg)
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 2
        assert messages[0].id == "msg_001"
        assert messages[1].id == "msg_002"

    def test_tasks_flow(self, clean_data_dir):
        """Test: append task → read task → update status"""
        user_id = 123456789
        fm = FileManager()
        
        task = Task(
            id="task_001",
            title="Подготовить отчёт",
            tags=["работа", "отчёт"],
            status="pending",
            created_at=datetime(2026, 3, 6, 14, 30, 0),
            source_message_ids=["msg_001", "msg_002"],
            content="Собрать данные и написать отчёт"
        )
        
        fm.append_task(user_id, task)
        
        tasks = fm.read_tasks(user_id)
        
        assert len(tasks) == 1
        assert tasks[0].title == "Подготовить отчёт"
        assert tasks[0].status == "pending"
        
        fm.update_task_status(user_id, "task_001", "completed")
        
        tasks = fm.read_tasks(user_id)
        assert tasks[0].status == "completed"

    def test_notes_flow(self, clean_data_dir):
        """Test: append note → read all notes"""
        user_id = 123456789
        fm = FileManager()
        
        note = Note(
            id="note_001",
            title="Идея async/await",
            tags=["идеи", "разработка"],
            created_at=datetime(2026, 3, 6, 14, 30, 0),
            source_message_ids=["msg_003"],
            content="Предложено использовать async/await"
        )
        
        fm.append_note(user_id, note)
        
        notes = fm.read_notes(user_id)
        
        assert len(notes) == 1
        assert notes[0].title == "Идея async/await"

    def test_nonexistent_user(self, clean_data_dir):
        """Test: read messages for non-existent user returns empty list"""
        fm = FileManager()
        
        messages = fm.read_messages(999999)
        
        assert len(messages) == 0

    def test_persistent_storage(self, clean_data_dir, sample_message):
        """Test: data persists across FileManager instances"""
        user_id = 123456789
        
        fm1 = FileManager()
        fm1.append_message(user_id, sample_message)
        
        fm2 = FileManager()
        messages = fm2.read_messages(user_id)
        
        assert len(messages) == 1
        assert messages[0].content == sample_message.content


class TestOllamaClientIntegration:
    """Integration tests for OllamaClient with error handling"""

    @pytest.mark.asyncio
    async def test_summarize_with_connect_error(self, clean_data_dir):
        """Test: Ollama unavailable → skip with proper reason"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Тест",
                chat_id=-1001234567890
            )
        ]
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            client = OllamaClient()
            result = await client.summarize_group(messages)
            
            assert result["action"] == "skip"
            assert "Ollama not available" in result["reason"]

    @pytest.mark.asyncio
    async def test_summarize_with_timeout(self, clean_data_dir):
        """Test: timeout → skip with proper reason"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Тест",
                chat_id=-1001234567890
            )
        ]
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")
            
            client = OllamaClient()
            result = await client.summarize_group(messages)
            
            assert result["action"] == "skip"
            assert "timeout" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_summarize_with_http_error(self, clean_data_dir):
        """Test: HTTP error → skip with status code"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Тест",
                chat_id=-1001234567890
            )
        ]
        
        mock_response = MagicMock(status_code=500)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(),
            response=mock_response
        )
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            client = OllamaClient()
            result = await client.summarize_group(messages)
            
            assert result["action"] == "skip"
            assert "500" in result["reason"]

    @pytest.mark.asyncio
    async def test_summarize_empty_messages(self, clean_data_dir):
        """Test: empty messages → skip"""
        client = OllamaClient()
        result = await client.summarize_group([])
        
        assert result["action"] == "skip"
        assert "Empty" in result["reason"]

    @pytest.mark.asyncio
    async def test_summarize_successful_response(self, clean_data_dir):
        """Test: successful Ollama response → parse task"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Нужно подготовить отчёт",
                chat_id=-1001234567890
            )
        ]
        
        mock_response = {
            "response": '{"action": "create_task", "title": "Подготовить отчёт", "tags": ["работа"], "content": "Создать отчёт", "reason": "Есть задача"}'
        }
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            client = OllamaClient()
            result = await client.summarize_group(messages)
            
            assert result["action"] == "create_task"
            assert result["title"] == "Подготовить отчёт"
            assert "работа" in result["tags"]


class TestContextAnalyzerIntegration:
    """Integration tests for ContextAnalyzer"""

    def test_group_by_time_window(self):
        """Test: messages within time window are grouped"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Первое сообщение",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 14, 20, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Второе сообщение (продолжение)",
                chat_id=-1001234567890
            ),
        ]
        
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_group_separate_time_windows(self):
        """Test: messages far apart are in separate groups"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Первое сообщение",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 16, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Сообщение через 2 часа",
                chat_id=-1001234567890
            ),
        ]
        
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        assert len(groups) == 2

    def test_group_by_similarity(self):
        """Test: messages with common keywords are grouped"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Нужно купить продукты: хлеб, молоко, яйца",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 14, 5, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Ещё нужно купить масло и сыр",
                chat_id=-1001234567890
            ),
        ]
        
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        assert len(groups) == 1
        assert len(groups[0]) == 2


class TestAutoSummarizeIntegration:
    """Integration tests for auto_summarize handler"""

    @pytest.mark.asyncio
    async def test_auto_summarize_with_messages(self, clean_data_dir):
        """Test: messages in inbox → tasks/notes created → inbox cleared"""
        user_id = 123456789
        fm = FileManager()
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=user_id,
                sender_id=user_id,
                sender_name="Test User",
                content="Нужно подготовить отчёт по проекту до завтра",
                chat_id=-1001234567890
            ),
        ]
        
        for msg in messages:
            fm.append_message(user_id, msg)
        
        mock_response = {
            "response": '{"action": "create_task", "title": "Подготовить отчёт по проекту", "tags": ["работа"], "content": "Создать отчёт", "reason": "Есть задача"}'
        }
        
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            await auto_summarize(user_id, bot=mock_bot)
            
            tasks = fm.read_tasks(user_id)
            assert len(tasks) == 1
            assert tasks[0].title == "Подготовить отчёт по проекту"
            
            inbox_messages = fm.read_messages(user_id)
            assert len(inbox_messages) == 0
            
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_summarize_empty_inbox(self, clean_data_dir):
        """Test: empty inbox → appropriate message to user"""
        user_id = 123456789
        
        mock_bot = AsyncMock()
        
        await auto_summarize(user_id, bot=mock_bot)
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[0][1]
        assert "пуст" in call_args.lower() or "ничего" in call_args.lower()

    @pytest.mark.asyncio
    async def test_auto_summarize_ollama_unavailable(self, clean_data_dir):
        """Test: Ollama unavailable → inbox cleared → error message"""
        user_id = 123456789
        fm = FileManager()
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=user_id,
                sender_id=user_id,
                sender_name="Test",
                content="Тест сообщение",
                chat_id=-1001234567890
            ),
        ]
        
        for msg in messages:
            fm.append_message(user_id, msg)
        
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            await auto_summarize(user_id, bot=mock_bot)
            
            inbox_messages = fm.read_messages(user_id)
            assert len(inbox_messages) == 0
            
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_summarize_multiple_groups(self, clean_data_dir):
        """Test: multiple message groups → multiple tasks/notes"""
        user_id = 123456789
        fm = FileManager()
        
        # Use messages far enough apart to be in separate groups (>30 min)
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=user_id,
                sender_id=user_id,
                sender_name="Test",
                content="Нужно купить продукты",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 15, 0, 0),
                from_user=user_id,
                sender_id=user_id,
                sender_name="Test",
                content="Сохрани идею: использовать async/await",
                chat_id=-1001234567890
            ),
        ]
        
        for msg in messages:
            fm.append_message(user_id, msg)
        
        mock_response_task = {
            "response": '{"action": "create_task", "title": "Купить продукты", "tags": ["покупки"], "content": "Купить продукты", "reason": "Задача"}'
        }
        mock_response_note = {
            "response": '{"action": "create_note", "title": "Идея async/await", "tags": ["идеи"], "content": "Использовать async/await", "reason": "Заметка"}'
        }
        
        mock_bot = AsyncMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                MagicMock(json=MagicMock(return_value=mock_response_task), raise_for_status=MagicMock()),
                MagicMock(json=MagicMock(return_value=mock_response_note), raise_for_status=MagicMock()),
            ]
            
            await auto_summarize(user_id, bot=mock_bot)
            
            tasks = fm.read_tasks(user_id)
            notes = fm.read_notes(user_id)
            
            assert len(tasks) >= 1
            assert len(notes) >= 1
            
            inbox_messages = fm.read_messages(user_id)
            assert len(inbox_messages) == 0


class TestEdgeCases:
    """Edge case handling tests"""

    def test_message_without_sender_name(self, clean_data_dir):
        """Test: message with sender_name=None handled correctly"""
        user_id = 123456789
        fm = FileManager()
        
        message = InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name=None,
            content="Тест",
            chat_id=-1001234567890
        )
        
        fm.append_message(user_id, message)
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert messages[0].sender_name is None

    def test_very_long_message(self, clean_data_dir):
        """Test: very long message (>4096 chars) handled"""
        user_id = 123456789
        fm = FileManager()
        
        long_content = "Это очень длинное сообщение " * 200
        message = InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content=long_content,
            chat_id=-1001234567890
        )
        
        fm.append_message(user_id, message)
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert len(messages[0].content) > 4096

    def test_special_characters_in_content(self, clean_data_dir):
        """Test: messages with special characters and unicode"""
        user_id = 123456789
        fm = FileManager()
        
        message = InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Иван Иванов",
            content="Привет! Это тест с unicode: 日本語 🎉 <tags> & symbols",
            chat_id=-1001234567890
        )
        
        fm.append_message(user_id, message)
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 1
        assert "unicode" in messages[0].content
        assert "日本語" in messages[0].content

    def test_many_messages_same_user(self, clean_data_dir):
        """Test: many messages from same user handled"""
        user_id = 123456789
        fm = FileManager()
        
        for i in range(50):
            message = InboxMessage(
                id=f"msg_{i:03d}",
                timestamp=datetime(2026, 3, 6, 14, i, 0),
                from_user=user_id,
                sender_id=user_id,
                sender_name="Test",
                content=f"Сообщение {i}",
                chat_id=-1001234567890
            )
            fm.append_message(user_id, message)
        
        messages = fm.read_messages(user_id)
        
        assert len(messages) == 50
        assert messages[0].content == "Сообщение 0"
        assert messages[49].content == "Сообщение 49"

    def test_multiple_users_isolation(self, clean_data_dir):
        """Test: data isolation between different users"""
        fm = FileManager()
        
        user1_messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=111111111,
                sender_id=111111111,
                sender_name="User1",
                content="Сообщение пользователя 1",
                chat_id=-1001234567890
            )
        ]
        
        user2_messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=222222222,
                sender_id=222222222,
                sender_name="User2",
                content="Сообщение пользователя 2",
                chat_id=-1001234567890
            )
        ]
        
        for msg in user1_messages:
            fm.append_message(111111111, msg)
        
        for msg in user2_messages:
            fm.append_message(222222222, msg)
        
        messages1 = fm.read_messages(111111111)
        messages2 = fm.read_messages(222222222)
        
        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0].content == "Сообщение пользователя 1"
        assert messages2[0].content == "Сообщение пользователя 2"


class TestBotCommandsIntegration:
    """Integration tests for bot commands - testing core functionality"""

    @pytest.mark.asyncio
    async def test_command_start_data(self, clean_data_dir):
        """Test: /start command data - statistics available"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Тест задача",
            tags=["test"],
            status="pending",
            created_at=datetime(2026, 3, 6, 14, 0, 0),
            source_message_ids=["msg_001"],
            content="Content"
        ))
        
        fm.append_note(user_id, Note(
            id="note_001",
            title="Тест заметка",
            tags=["test"],
            created_at=datetime(2026, 3, 6, 14, 0, 0),
            source_message_ids=["msg_002"],
            content="Content"
        ))
        
        fm.append_message(user_id, InboxMessage(
            id="msg_003",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Тест",
            chat_id=-1001234567890
        ))
        
        tasks = fm.read_tasks(user_id)
        notes = fm.read_notes(user_id)
        messages = fm.read_messages(user_id)
        
        assert len(tasks) == 1
        assert len(notes) == 1
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_command_inbox_data(self, clean_data_dir):
        """Test: /inbox command data - messages retrievable"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_message(user_id, InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test",
            content="Тестовое сообщение",
            chat_id=-1001234567890
        ))
        
        messages = fm.read_messages(user_id)
        assert len(messages) == 1
        assert messages[0].content == "Тестовое сообщение"

    @pytest.mark.asyncio
    async def test_command_tasks_data(self, clean_data_dir):
        """Test: /tasks command data - tasks retrievable"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_task(user_id, Task(
            id="task_001",
            title="Тест задача",
            tags=["test"],
            status="pending",
            created_at=datetime(2026, 3, 6, 14, 0, 0),
            source_message_ids=["msg_001"],
            content="Content"
        ))
        
        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].title == "Тест задача"

    @pytest.mark.asyncio
    async def test_command_notes_data(self, clean_data_dir):
        """Test: /notes command data - notes retrievable"""
        user_id = 123456789
        fm = FileManager()
        
        fm.append_note(user_id, Note(
            id="note_001",
            title="Тест заметка",
            tags=["test"],
            created_at=datetime(2026, 3, 6, 14, 0, 0),
            source_message_ids=["msg_001"],
            content="Content"
        ))
        
        notes = fm.read_notes(user_id)
        assert len(notes) == 1
        assert notes[0].title == "Тест заметка"

    @pytest.mark.asyncio
    async def test_command_summarize_empty_inbox(self, clean_data_dir):
        """Test: /summarize with empty inbox"""
        user_id = 123456789
        
        mock_bot = AsyncMock()
        
        await auto_summarize(user_id, bot=mock_bot)
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[0][1]
        assert "пуст" in call_args.lower() or "ничего" in call_args.lower()


@pytest.mark.asyncio
async def test_end_to_end_message_flow(clean_data_dir):
    """E2E: Send message → store in inbox → auto_summarize → verify tasks/notes → inbox cleared"""
    user_id = 123456789
    fm = FileManager()
    
    message = InboxMessage(
        id="msg_001",
        timestamp=datetime(2026, 3, 6, 14, 0, 0),
        from_user=user_id,
        sender_id=user_id,
        sender_name="Test User",
        content="Нужно подготовить отчёт по проекту до завтра к обеду",
        chat_id=-1001234567890
    )
    
    fm.append_message(user_id, message)
    
    messages = fm.read_messages(user_id)
    assert len(messages) == 1
    
    mock_response = {
        "response": '{"action": "create_task", "title": "Подготовить отчёт по проекту", "tags": ["работа", "отчёт"], "content": "Подготовить отчёт до завтра к обеду", "reason": "Есть задача"}'
    }
    
    mock_bot = AsyncMock()
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        await auto_summarize(user_id, bot=mock_bot)
        
        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].title == "Подготовить отчёт по проекту"
        assert "работа" in tasks[0].tags
        assert "отчёт" in tasks[0].tags
        
        inbox_messages = fm.read_messages(user_id)
        assert len(inbox_messages) == 0


@pytest.mark.asyncio
async def test_end_to_end_forwarded_message(clean_data_dir):
    """E2E: Forwarded message → store with correct sender info → process"""
    user_id = 123456789
    fm = FileManager()
    
    message = InboxMessage(
        id="msg_001",
        timestamp=datetime(2026, 3, 6, 14, 0, 0),
        from_user=user_id,
        sender_id=987654321,
        sender_name="Original Author",
        content="Важная информация из канала",
        chat_id=-1001234567890
    )
    
    fm.append_message(user_id, message)
    
    messages = fm.read_messages(user_id)
    assert len(messages) == 1
    assert messages[0].sender_id == 987654321
    assert messages[0].sender_name == "Original Author"
    assert messages[0].from_user == 123456789