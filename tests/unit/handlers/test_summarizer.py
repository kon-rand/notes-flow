import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from bot.db.models import InboxMessage
from bot.db.file_manager import FileManager
from handlers.summarizer import auto_summarize


@pytest.fixture
def sample_messages():
    """Тестовые сообщения"""
    now = datetime.now()
    return [
        InboxMessage(
            id="msg1",
            from_user=123,
            sender_id=123,
            sender_name="Test User",
            content="Купить молоко",
            timestamp=now - timedelta(minutes=10),
            chat_id=123
        ),
        InboxMessage(
            id="msg2",
            from_user=123,
            sender_id=123,
            sender_name="Test User",
            content="Позвонить маме",
            timestamp=now - timedelta(minutes=5),
            chat_id=123
        )
    ]


@pytest.fixture
def mock_file_manager():
    """Mock FileManager"""
    return MagicMock(spec=FileManager)


@pytest.fixture
def mock_bot():
    """Mock Telegram bot"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_auto_summarize_empty_inbox(mock_bot):
    """Тест: пустой инбокс"""
    with patch('handlers.summarizer.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.read_messages.return_value = []
        MockFM.return_value = fm_instance
        
        result = await auto_summarize(123, mock_bot)
        
        assert result is None
        fm_instance.read_messages.assert_called_once_with(123)
        fm_instance.clear_messages.assert_not_called()


@pytest.mark.asyncio
async def test_auto_summarize_single_task(mock_bot, sample_messages, mock_file_manager):
    """Тест: создание одной задачи через summarize_messages"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "create_task",
            "title": "Купить молоко и позвонить маме",
            "tags": ["покупки", "семья"],
            "content": "Нужно купить молоко и позвонить маме",
            "source_message_ids": ["msg1", "msg2"]
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_task = MagicMock()
        
        await auto_summarize(123, mock_bot)
        
        client_instance.summarize_messages.assert_called_once_with(sample_messages)


@pytest.mark.asyncio
async def test_auto_summarize_create_task(mock_bot, sample_messages, mock_file_manager):
    """Тест: создание задачи через summarize_messages"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "create_task",
            "title": "Купить продукты",
            "tags": ["покупки"],
            "content": "Список продуктов",
            "source_message_ids": ["msg1"]
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_task = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 0
        mock_file_manager.append_task.assert_called_once()


@pytest.mark.asyncio
async def test_auto_summarize_create_note(mock_bot, sample_messages, mock_file_manager):
    """Тест: создание заметки через summarize_messages"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "create_note",
            "title": "Идеи для проекта",
            "tags": ["ideas"],
            "content": "Концепция проекта",
            "source_message_ids": ["msg2"]
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_note = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 1
        mock_file_manager.append_note.assert_called_once()


@pytest.mark.asyncio
async def test_auto_summarize_skip_action(mock_bot, sample_messages, mock_file_manager):
    """Тест: пропуск сообщений через summarize_messages"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "skip",
            "reason": "Not important"
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["skipped"] == 1
        assert result["tasks_created"] == 0


@pytest.mark.asyncio
async def test_auto_summarize_clear_inbox(mock_bot, sample_messages, mock_file_manager):
    """Тест: очистка инбокса после обработки"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "create_task",
            "title": "Тестовая задача",
            "tags": [],
            "content": "",
            "source_message_ids": ["msg1"]
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        await auto_summarize(123, mock_bot)
        
        mock_file_manager.clear_messages.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_auto_summarize_send_report(mock_bot, sample_messages, mock_file_manager):
    """Тест: отправка отчёта о результатах"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[{
            "action": "create_task",
            "title": "Тестовая задача",
            "tags": [],
            "content": "",
            "source_message_ids": ["msg1"]
        }])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        await auto_summarize(123, mock_bot)
        
        mock_bot.send_message.assert_called_once()
        report_text = mock_bot.send_message.call_args[0][1]
        assert "Саммаризация завершена" in report_text
        assert "Задачи создано: 1" in report_text


@pytest.mark.asyncio
async def test_auto_summarize_error_handling(mock_bot, sample_messages, mock_file_manager):
    """Тест: обработка ошибок и отправка сообщения об ошибке"""
    from utils.error_types import LLMError
    
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(side_effect=LLMError("Test error"))
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert "error" in result
        mock_bot.send_message.assert_called_once()
        assert "Ошибка" in mock_bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_auto_summarize_multiple_results(mock_bot, mock_file_manager):
    """Тест: несколько результатов в одном ответе (задачи + заметки)"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Task 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Task 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789),
            InboxMessage(id="m3", from_user=123, sender_id=123, sender_name="User", content="Note 1", 
                        timestamp=now - timedelta(minutes=5), chat_id=123456789)
        ]
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[
            {"action": "create_task", "title": "Задача 1", "tags": [], "content": "", "source_message_ids": ["m1"]},
            {"action": "create_task", "title": "Задача 2", "tags": [], "content": "", "source_message_ids": ["m2"]},
            {"action": "create_note", "title": "Заметка 1", "tags": [], "content": "", "source_message_ids": ["m3"]}
        ])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        mock_file_manager.append_task = MagicMock()
        mock_file_manager.append_note = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 2
        assert result["notes_created"] == 1


@pytest.mark.asyncio
async def test_auto_summarize_all_skipped(mock_bot, mock_file_manager):
    """Тест: все сообщения пропущены"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Skip 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Skip 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789)
        ]
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[
            {"action": "skip", "reason": "Not important"}
        ])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["skipped"] == 1
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 0


@pytest.mark.asyncio
async def test_auto_summarize_only_tasks(mock_bot, mock_file_manager):
    """Тест: только задачи создаются"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Task 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Task 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789)
        ]
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[
            {"action": "create_task", "title": "Тестовая задача", "tags": [], "content": "", "source_message_ids": ["m1", "m2"]}
        ])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 0


@pytest.mark.asyncio
async def test_auto_summarize_only_notes(mock_bot, mock_file_manager):
    """Тест: только заметки создаются"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Note 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789)
        ]
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[
            {"action": "create_note", "title": "Тестовая заметка", "tags": [], "content": "", "source_message_ids": ["m1"]}
        ])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 1


@pytest.mark.asyncio
async def test_auto_summarize_empty_results_array(mock_bot, sample_messages, mock_file_manager):
    """Тест: пустой массив результатов от LLM"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.OpenAIClient') as MockClient:
        
        client_instance = MagicMock()
        client_instance.summarize_messages = AsyncMock(return_value=[])
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result is not None
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 0
        assert result["skipped"] == 0