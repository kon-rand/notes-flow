import pytest
import asyncio
from datetime import datetime
import shutil
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage, Task
from utils.ollama_client import OpenAIClient
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
def test_user_id():
    """Test user ID for isolation"""
    return 999999


class TestSummarizerIntegration:
    """Интеграционные тесты саммаризации"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, clean_data_dir, test_user_id):
        """Подготовка и очистка тестовых данных"""
        file_manager = FileManager()
        file_manager.clear_messages(test_user_id)
        yield
        file_manager.clear_messages(test_user_id)
    
    def test_load_messages_from_inbox(self, test_user_id):
        """Тест загрузки сообщений из инбокса"""
        file_manager = FileManager()
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test User",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test User",
                content="Да, конечно",
                chat_id=-1001234567890
            )
        ]
        
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        loaded = file_manager.read_messages(test_user_id)
        
        assert len(loaded) == 2
        assert loaded[0].content == "А сушилку сможешь разобрать?"
    
    @pytest.mark.asyncio
    async def test_ollama_api_call(self, test_user_id, clean_data_dir):
        """Тест вызова Ollama API с реальными данными"""
        file_manager = FileManager()
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test User",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            )
        ]
        
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        loaded = file_manager.read_messages(test_user_id)
        assert len(loaded) == 1
        
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(loaded)
        
        client = OpenAIClient()
        result = await client.summarize_group(groups[0])
        
        assert "action" in result
        assert result["action"] in ["create_task", "create_note", "skip"]
        
        print(f"\n=== Ollama Response ===")
        print(f"Action: {result.get('action')}")
        print(f"Title: {result.get('title')}")
        print(f"Tags: {result.get('tags')}")
        print(f"Content: {result.get('content')}")
        print(f"======================\n")
    
    @pytest.mark.asyncio
    async def test_full_summarization_flow(self, test_user_id, clean_data_dir):
        """Тест полной цепочки саммаризации"""
        from unittest.mock import AsyncMock
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Тест",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        loaded = file_manager.read_messages(test_user_id)
        assert len(loaded) == 1
        
        bot = AsyncMock()
        result = await auto_summarize(test_user_id, bot)
        
        assert "error" not in result or result.get("error") is None
        
        tasks = file_manager.read_tasks(test_user_id)
        assert len(tasks) > 0
        
        inbox = file_manager.read_messages(test_user_id)
        assert len(inbox) == 0
        
        print(f"\n=== Created Task ===")
        for task in tasks:
            print(f"ID: {task.id}")
            print(f"Title: {task.title}")
            print(f"Tags: {task.tags}")
            print(f"==================\n")
    
    def test_current_inbox_data(self, test_user_id, clean_data_dir):
        """Тест с реальными данными из текущего инбокса"""
        file_manager = FileManager()
        real_messages = file_manager.read_messages(61395267)
        
        if not real_messages:
            pytest.skip("Нет данных в инбоксе для тестирования")
        
        print(f"\n=== Real Inbox Data ===")
        print(f"User ID: 61395267")
        print(f"Messages count: {len(real_messages)}")
        for msg in real_messages:
            print(f"- {msg.id}: {msg.content[:100]}...")
        print(f"=======================\n")
        
        assert len(real_messages) > 0
    
    @pytest.mark.asyncio
    async def test_llm_parsing_error_handling(self, test_user_id, clean_data_dir):
        """Тест обработки ошибок парсинга ответа LLM"""
        from unittest.mock import AsyncMock, patch
        
        file_manager = FileManager()
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Тестовое сообщение",
                chat_id=-1001234567890
            )
        ]
        
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        with patch.object(OpenAIClient, 'summarize_group', new=AsyncMock(return_value={"action": "skip"})):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
            
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])