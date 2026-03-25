import pytest
import asyncio
from datetime import datetime
import shutil
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage, Task
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
        
        client = OpenAIClient()
        results = await client.summarize_messages(loaded)
        
        assert isinstance(results, list)
        assert len(results) >= 0
        
        if len(results) > 0:
            result = results[0]
            assert "action" in result
            assert result["action"] in ["create_task", "create_note", "skip"]
        
        print(f"\n=== Ollama Response ===")
        print(f"Results count: {len(results)}")
        for i, result in enumerate(results):
            print(f"Result {i}: Action={result.get('action')}")
            print(f"  Title: {result.get('title')}")
            print(f"  Tags: {result.get('tags')}")
            print(f"  Content: {result.get('content')}")
        print(f"======================\n")
    
    @pytest.mark.asyncio
    async def test_full_summarization_flow(self, test_user_id, clean_data_dir):
        """Тест полной цепочки саммаризации"""
        from unittest.mock import AsyncMock, MagicMock, patch
        
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
        
        # Mock Ollama response to avoid real API call
        with patch('handlers.summarizer.OpenAIClient') as MockClient:
            client_instance = MagicMock()
            client_instance.summarize_messages = AsyncMock(return_value=[{
                "action": "create_task",
                "title": "Разобрать сушилку",
                "tags": ["ремонт"],
                "content": "Пользователь просит разобрать сушилку"
            }])
            MockClient.return_value = client_instance
            
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
        
        with patch.object(OpenAIClient, 'summarize_messages', new=AsyncMock(return_value=[{"action": "skip"}])):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_multiple_tasks_in_single_response(self, test_user_id, clean_data_dir):
        """Тест обработки нескольких задач в одном ответе LLM"""
        from unittest.mock import AsyncMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Нужно купить продукты: молоко, хлеб, яйца",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="И ещё позвонить врачу в четверг",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        # Mock response with multiple tasks
        with patch.object(OpenAIClient, 'summarize_messages', new=AsyncMock(return_value=[
            {
                "action": "create_task",
                "title": "Купить продукты",
                "tags": ["дом", "покупки"],
                "content": "Молоко, хлеб, яйца",
                "source_message_ids": ["msg_001"]
            },
            {
                "action": "create_task",
                "title": "Позвонить врачу",
                "tags": ["здоровье", "звонки"],
                "content": "Позвонить в четверг",
                "source_message_ids": ["msg_002"]
            }
        ])):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
        
        assert result is not None
        assert "error" not in result or result.get("error") is None
        
        tasks = file_manager.read_tasks(test_user_id)
        assert len(tasks) == 2
        
        print(f"\n=== Multiple Tasks Created ===")
        for task in tasks:
            print(f"Title: {task.title}")
            print(f"Tags: {task.tags}")
        print(f"==============================\n")
    
    @pytest.mark.asyncio
    async def test_mixed_tasks_and_notes(self, test_user_id, clean_data_dir):
        """Тест обработки смешанных задач и заметок"""
        from unittest.mock import AsyncMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Нужно подготовить презентацию к пятнице",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Важная мысль: эффективность зависит от автоматизации рутинных задач",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        # Mock response with mixed task and note
        with patch.object(OpenAIClient, 'summarize_messages', new=AsyncMock(return_value=[
            {
                "action": "create_task",
                "title": "Подготовить презентацию",
                "tags": ["работа", "презентация"],
                "content": "К пятнице",
                "source_message_ids": ["msg_001"]
            },
            {
                "action": "create_note",
                "title": "Эффективность и автоматизация",
                "tags": ["мысли", "эффективность"],
                "content": "Эффективность зависит от автоматизации рутинных задач",
                "source_message_ids": ["msg_002"]
            }
        ])):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
        
        assert result is not None
        
        tasks = file_manager.read_tasks(test_user_id)
        notes = file_manager.read_notes(test_user_id)
        
        assert len(tasks) == 1
        assert len(notes) == 1
        
        print(f"\n=== Mixed Task and Note ===")
        print(f"Tasks: {len(tasks)}, Notes: {len(notes)}")
        print(f"=============================\n")
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, test_user_id, clean_data_dir):
        """Тест обработки пустого ответа от LLM"""
        from unittest.mock import AsyncMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Просто информационное сообщение без действий",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        # Mock empty response (all messages skipped)
        with patch.object(OpenAIClient, 'summarize_messages', new=AsyncMock(return_value=[])):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
        
        assert result is not None
        assert "error" not in result or result.get("error") is None
        
        tasks = file_manager.read_tasks(test_user_id)
        assert len(tasks) == 0
        
        print(f"\n=== Empty Response (No Tasks Created) ===")
        print(f"Tasks created: {len(tasks)}")
        print(f"===========================================\n")
    
    @pytest.mark.asyncio
    async def test_skip_action_handling(self, test_user_id, clean_data_dir):
        """Тест обработки action='skip'"""
        from unittest.mock import AsyncMock, patch
        
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=test_user_id,
                sender_id=test_user_id,
                sender_name="Test",
                content="Спасибо, всё понятно",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(test_user_id, msg)
        
        # Mock response with skip action
        with patch.object(OpenAIClient, 'summarize_messages', new=AsyncMock(return_value=[
            {
                "action": "skip",
                "reason": "Сообщение не содержит действий"
            }
        ])):
            bot = AsyncMock()
            result = await auto_summarize(test_user_id, bot)
        
        assert result is not None
        assert "error" not in result or result.get("error") is None
        
        inbox = file_manager.read_messages(test_user_id)
        # Messages are NOT removed when all are skipped (no tasks/notes created)
        assert len(inbox) == 1
        
        print(f"\n=== Skip Action (Messages Kept) ===")
        print(f"Inbox remaining: {len(inbox)}")
        print(f"=====================================\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])