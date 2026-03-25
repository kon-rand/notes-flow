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
from utils.ollama_client import OpenAIClient
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

    def test_read_nonexistent_user(self, clean_data_dir):
        """Test: read messages for user with no data"""
        fm = FileManager()
        messages = fm.read_messages(999999)
        
        assert len(messages) == 0


class TestOllamaClientIntegration:
    """Integration tests for OllamaClient"""

    @pytest.mark.asyncio
    async def test_summarize_messages_connection_error(self, clean_data_dir):
        """Test: connection error → return empty array"""
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
            
            client = OpenAIClient()
            result = await client.summarize_messages(messages)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_summarize_messages_with_timeout(self, clean_data_dir):
        """Test: timeout → return empty array"""
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
            
            client = OpenAIClient()
            result = await client.summarize_messages(messages)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_summarize_messages_with_http_error(self, clean_data_dir):
        """Test: HTTP error → return empty array"""
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
            
            client = OpenAIClient()
            result = await client.summarize_messages(messages)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_summarize_messages_empty_list(self, clean_data_dir):
        """Test: empty messages list → return empty array"""
        client = OpenAIClient()
        result = await client.summarize_messages([])
        
        assert result == []

    @pytest.mark.asyncio
    async def test_summarize_messages_successful_response(self, clean_data_dir):
        """Test: successful Ollama response → parse array of results"""
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
            "choices": [{
                "message": {
                    "content": '[{"action": "create_task", "title": "Подготовить отчёт", "tags": ["работа"], "content": "Создать отчёт", "source_message_ids": ["msg_001"]}]'
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                text=mock_response["choices"][0]["message"]["content"],
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            client = OpenAIClient()
            result = await client.summarize_messages(messages)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["action"] == "create_task"
            assert result[0]["title"] == "Подготовить отчёт"
            assert "работа" in result[0]["tags"]

    @pytest.mark.asyncio
    async def test_summarize_messages_multiple_results(self, clean_data_dir):
        """Test: multiple tasks/notes in single response"""
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Нужно купить продукты",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 14, 1, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="И позвонить врачу",
                chat_id=-1001234567890
            )
        ]
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": '[{"action": "create_task", "title": "Купить продукты", "tags": ["дом"], "content": "Хлеб, молоко", "source_message_ids": ["msg_001"]}, {"action": "create_task", "title": "Позвонить врачу", "tags": ["здоровье"], "content": "Записаться на приём", "source_message_ids": ["msg_002"]}]'
                }
            }]
        }
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                text=mock_response["choices"][0]["message"]["content"],
                json=MagicMock(return_value=mock_response),
                raise_for_status=MagicMock()
            )
            
            client = OpenAIClient()
            result = await client.summarize_messages(messages)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["action"] == "create_task"
            assert result[1]["action"] == "create_task"


class TestAutoSummarizeIntegration:
    """Integration tests for auto_summarize handler"""

    @pytest.mark.asyncio
    async def test_auto_summarize_full_flow(self, clean_data_dir):
        """Test: complete summarization flow with task creation"""
        from unittest.mock import AsyncMock, MagicMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Нужно подготовить отчёт по проекту",
                chat_id=-1001234567890
            )
        ]
        
        fm = FileManager()
        for msg in messages:
            fm.append_message(123456789, msg)
        
        bot = AsyncMock()
        
        with patch('handlers.summarizer.OpenAIClient') as MockClient:
            client_instance = MagicMock()
            client_instance.summarize_messages = AsyncMock(return_value=[{
                "action": "create_task",
                "title": "Подготовить отчёт по проекту",
                "tags": ["работа", "отчёт"],
                "content": "Собрать данные и написать отчёт",
                "source_message_ids": ["msg_001"]
            }])
            MockClient.return_value = client_instance
            
            result = await auto_summarize(123456789, bot)
        
        assert result is not None
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 0
        
        # Verify inbox was cleared
        remaining_messages = fm.read_messages(123456789)
        assert len(remaining_messages) == 0
        
        # Verify task was created
        tasks = fm.read_tasks(123456789)
        assert len(tasks) == 1
        assert tasks[0].title == "Подготовить отчёт по проекту"
        
        # Verify report was sent
        bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_summarize_empty_inbox(self, clean_data_dir):
        """Test: empty inbox returns None"""
        bot = AsyncMock()
        
        result = await auto_summarize(999999, bot)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_summarize_mixed_results(self, clean_data_dir):
        """Test: mixed tasks and notes in single response"""
        from unittest.mock import AsyncMock, MagicMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime(2026, 3, 6, 14, 0, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Нужно купить молоко",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime(2026, 3, 6, 14, 1, 0),
                from_user=123456789,
                sender_id=123456789,
                sender_name="Test",
                content="Важно: эффективность зависит от автоматизации",
                chat_id=-1001234567890
            )
        ]
        
        fm = FileManager()
        for msg in messages:
            fm.append_message(123456789, msg)
        
        bot = AsyncMock()
        
        with patch('handlers.summarizer.OpenAIClient') as MockClient:
            client_instance = MagicMock()
            client_instance.summarize_messages = AsyncMock(return_value=[
                {
                    "action": "create_task",
                    "title": "Купить молоко",
                    "tags": ["дом", "покупки"],
                    "content": "Молоко",
                    "source_message_ids": ["msg_001"]
                },
                {
                    "action": "create_note",
                    "title": "Эффективность и автоматизация",
                    "tags": ["мысли", "эффективность"],
                    "content": "Эффективность зависит от автоматизации",
                    "source_message_ids": ["msg_002"]
                }
            ])
            MockClient.return_value = client_instance
            
            result = await auto_summarize(123456789, bot)
        
        assert result is not None
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])