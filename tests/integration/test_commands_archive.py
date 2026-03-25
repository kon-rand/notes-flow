import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from bot.db.models import Task
from handlers.commands import (
    archived_handler,
    archive_handler
)


@pytest.fixture
def mock_message():
    """Mock Telegram message"""
    msg = MagicMock()
    msg.from_user = AsyncMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock()
    msg.text = "/archived"
    return msg


@pytest.fixture
def sample_tasks():
    """Тестовые задачи для архива"""
    now = datetime.now()
    return [
        Task(
            id="task_001",
            title="Купить продукты",
            tags=["покупки"],
            status="completed",
            created_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1),
            archived_at=now - timedelta(days=1),
            source_message_ids=["msg1"],
            content="Молоко, хлеб, яйца"
        ),
        Task(
            id="task_002",
            title="Позвонить клиенту",
            tags=["работа"],
            status="completed",
            created_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1),
            archived_at=now - timedelta(days=1),
            source_message_ids=["msg2"],
            content="Обсудить проект"
        )
    ]


@pytest.mark.asyncio
async def test_archived_handler_no_archives(mock_message):
    """Тест: /archived без архивов"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_archive_dates.return_value = []
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "пока нет архивов" in response


@pytest.mark.asyncio
async def test_archived_handler_with_archives(mock_message, sample_tasks):
    """Тест: /archived с архивами"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_archive_dates.return_value = ["2026-03-10"]
        fm_instance.get_tasks_by_archive_date.return_value = sample_tasks
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Архивы задач" in response
        assert "/2026_03_10" in response
        assert "(2 задач)" in response


@pytest.mark.asyncio
async def test_archived_handler_with_date_invalid_format(mock_message):
    """Тест: /archived с некорректным форматом даты"""
    mock_message.text = "/archived invalid_date"
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        MockFM.return_value.get_archive_dates.assert_not_called()
        MockFM.return_value.get_tasks_by_archive_date.assert_not_called()
        mock_message.answer.assert_called_once()
        assert "Неверный формат даты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_archived_handler_with_date_no_tasks(mock_message):
    """Тест: /archived с датой, но без задач"""
    mock_message.text = "/archived 2026_03_10"
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_tasks_by_archive_date.return_value = []
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Задач за 2026-03-10 не найдено" in response


@pytest.mark.asyncio
async def test_archived_handler_with_date_with_tasks(mock_message, sample_tasks):
    """Тест: /archived с датой и задачами"""
    mock_message.text = "/archived 2026_03_10"
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_tasks_by_archive_date.return_value = sample_tasks
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Задачи за 2026-03-10" in response
        assert "Купить продукты" in response
        assert "[покупки]" in response
        assert "Позвонить клиенту" in response
        assert "[работа]" in response


@pytest.mark.asyncio
async def test_archived_handler_no_user(mock_message):
    """Тест: /archived без пользователя"""
    mock_message.from_user = None
    
    with patch('handlers.commands.FileManager') as MockFM:
        await archived_handler(mock_message)
        
        MockFM.assert_not_called()
        mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_archive_handler_no_completed_tasks(mock_message):
    """Тест: /archive без выполненных задач за сегодня"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.archive_completed_tasks.return_value = []
        MockFM.return_value = fm_instance
        
        await archive_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        assert f"Архивировано задач за {today}: 0" in response


@pytest.mark.asyncio
async def test_archive_handler_with_completed_tasks(mock_message, sample_tasks):
    """Тест: /archive с выполненными задачами за сегодня"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.archive_completed_tasks.return_value = sample_tasks
        MockFM.return_value = fm_instance
        
        await archive_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        assert f"Архивировано задач за {today}: 2" in response


@pytest.mark.asyncio
async def test_archive_handler_no_user(mock_message):
    """Тест: /archive без пользователя"""
    mock_message.from_user = None
    
    with patch('handlers.commands.FileManager') as MockFM:
        await archive_handler(mock_message)
        
        MockFM.assert_not_called()
        mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_archived_handler_with_empty_archives_list(mock_message):
    """Тест: /archived с пустым списком архивов"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_archive_dates.return_value = []
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "пока нет архивов" in response


@pytest.mark.asyncio
async def test_archived_handler_multiple_archive_dates(mock_message):
    """Тест: /archived с несколькими датами архивов"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_archive_dates.return_value = ["2026-03-08", "2026-03-09", "2026-03-10"]
        fm_instance.get_tasks_by_archive_date.side_effect = [
            [Task(
                id="task_001",
                title="Задача 1",
                tags=[],
                status="completed",
                created_at=datetime(2026, 3, 8),
                completed_at=datetime(2026, 3, 8),
                archived_at=datetime(2026, 3, 8),
                source_message_ids=["msg1"],
                content="Контент"
            )],
            [],
            [Task(
                id="task_002",
                title="Задача 2",
                tags=["test"],
                status="completed",
                created_at=datetime(2026, 3, 10),
                completed_at=datetime(2026, 3, 10),
                archived_at=datetime(2026, 3, 10),
                source_message_ids=["msg2"],
                content="Контент"
            )]
        ]
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "/2026_03_08" in response
        assert "/2026_03_09" in response
        assert "/2026_03_10" in response
        assert "(1 задач)" in response
        assert "(0 задач)" in response


@pytest.mark.asyncio
async def test_archived_handler_with_date_navigation_hint(mock_message, sample_tasks):
    """Тест: /archived с датой показывает задачи"""
    mock_message.text = "/archived 2026_03_10"
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_tasks_by_archive_date.return_value = sample_tasks
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Задачи за 2026-03-10" in response


@pytest.mark.asyncio
async def test_archived_handler_with_date_separate_format(mock_message, sample_tasks):
    """Тест: /archived в отдельном сообщении с датой"""
    mock_message.text = "/archived 2026_03_10"
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.get_tasks_by_archive_date.return_value = sample_tasks
        MockFM.return_value = fm_instance
        
        await archived_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Задачи за 2026-03-10" in response
        assert "Купить продукты" in response
        assert "[покупки]" in response