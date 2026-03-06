import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import List

from bot.db.models import InboxMessage
from bot.db.file_manager import FileManager
from utils.context_analyzer import ContextAnalyzer
from utils.ollama_client import OllamaClient
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
async def test_auto_summarize_group_messages(mock_bot, sample_messages, mock_file_manager):
    """Тест: группировка сообщений через ContextAnalyzer"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_task",
            "title": "Купить молоко и позвонить маме",
            "tags": ["покупки", "семья"],
            "content": "Нужно купить молоко и позвонить маме"
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_task = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        analyzer_instance.group_messages.assert_called_once_with(sample_messages)
        client_instance.summarize_group.assert_called_once_with(sample_messages)


@pytest.mark.asyncio
async def test_auto_summarize_create_task(mock_bot, sample_messages, mock_file_manager):
    """Тест: создание задачи через OllamaClient"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_task",
            "title": "Купить продукты",
            "tags": ["покупки"],
            "content": "Список продуктов"
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_task = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 0
        mock_file_manager.append_task.assert_called_once()


@pytest.mark.asyncio
async def test_auto_summarize_create_note(mock_bot, sample_messages, mock_file_manager):
    """Тест: создание заметки через OllamaClient"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_note",
            "title": "Идеи для проекта",
            "tags": ["ideas"],
            "content": "Концепция проекта"
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        mock_file_manager.append_note = MagicMock()
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 1
        mock_file_manager.append_note.assert_called_once()


@pytest.mark.asyncio
async def test_auto_summarize_skip_group(mock_bot, sample_messages, mock_file_manager):
    """Тест: пропуск групп через OllamaClient"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "skip",
            "reason": "Not important"
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["skipped"] == 1
        assert result["tasks_created"] == 0


@pytest.mark.asyncio
async def test_auto_summarize_clear_inbox(mock_bot, sample_messages, mock_file_manager):
    """Тест: очистка инбокса после обработки"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_task",
            "title": "Тестовая задача",
            "tags": [],
            "content": ""
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        await auto_summarize(123, mock_bot)
        
        mock_file_manager.clear_messages.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_auto_summarize_send_report(mock_bot, sample_messages, mock_file_manager):
    """Тест: отправка отчёта о результатах"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [sample_messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_task",
            "title": "Тестовая задача",
            "tags": [],
            "content": ""
        })
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
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer:
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.side_effect = Exception("Test error")
        MockAnalyzer.return_value = analyzer_instance
        
        mock_file_manager.read_messages.return_value = sample_messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert "error" in result
        mock_bot.send_message.assert_called_once()
        assert "Ошибка при саммаризации" in mock_bot.send_message.call_args[0][1]


@pytest.mark.asyncio
async def test_auto_summarize_multiple_groups(mock_bot, mock_file_manager):
    """Тест: несколько групп сообщений"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        now = datetime.now()
        group1 = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Task 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Task 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789)
        ]
        group2 = [
            InboxMessage(id="m3", from_user=123, sender_id=123, sender_name="User", content="Note 1", 
                        timestamp=now - timedelta(minutes=5), chat_id=123456789)
        ]
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [group1, group2]
        MockAnalyzer.return_value = analyzer_instance
        
        async def summarize_side_effect(group):
            if len(group) == 2:
                return {"action": "create_task", "title": "Задача из группы 1", "tags": [], "content": ""}
            else:
                return {"action": "create_note", "title": "Заметка из группы 2", "tags": [], "content": ""}
        
        client_instance = MagicMock()
        client_instance.summarize_group.side_effect = summarize_side_effect
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = group1 + group2
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 1
        assert client_instance.summarize_group.call_count == 2


@pytest.mark.asyncio
async def test_auto_summarize_all_skipped(mock_bot, mock_file_manager):
    """Тест: все группы пропущены"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Skip 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Skip 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789)
        ]
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={"action": "skip", "reason": "Not important"})
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
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Task 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789),
            InboxMessage(id="m2", from_user=123, sender_id=123, sender_name="User", content="Task 2", 
                        timestamp=now - timedelta(minutes=9), chat_id=123456789)
        ]
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_task",
            "title": "Тестовая задача",
            "tags": [],
            "content": ""
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 1
        assert result["notes_created"] == 0


@pytest.mark.asyncio
async def test_auto_summarize_only_notes(mock_bot, mock_file_manager):
    """Тест: только заметки создаются"""
    with patch('handlers.summarizer.FileManager', return_value=mock_file_manager), \
         patch('handlers.summarizer.ContextAnalyzer') as MockAnalyzer, \
         patch('handlers.summarizer.OllamaClient') as MockClient:
        
        now = datetime.now()
        messages = [
            InboxMessage(id="m1", from_user=123, sender_id=123, sender_name="User", content="Note 1", 
                        timestamp=now - timedelta(minutes=10), chat_id=123456789)
        ]
        
        analyzer_instance = MagicMock()
        analyzer_instance.group_messages.return_value = [messages]
        MockAnalyzer.return_value = analyzer_instance
        
        client_instance = MagicMock()
        client_instance.summarize_group = AsyncMock(return_value={
            "action": "create_note",
            "title": "Тестовая заметка",
            "tags": [],
            "content": ""
        })
        MockClient.return_value = client_instance
        
        mock_file_manager.read_messages.return_value = messages
        
        result = await auto_summarize(123, mock_bot)
        
        assert result["tasks_created"] == 0
        assert result["notes_created"] == 1