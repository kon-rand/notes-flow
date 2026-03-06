import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from bot.db.models import InboxMessage, Task, Note
from handlers.commands import (
    start_handler,
    help_handler,
    summarize_handler,
    inbox_handler,
    tasks_handler,
    notes_handler,
    clear_handler,
    settings_handler
)


@pytest.fixture
def mock_message():
    """Mock Telegram message"""
    msg = AsyncMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock()
    msg.text = "/start"
    return msg


@pytest.fixture
def sample_task():
    """Тестовая задача"""
    return Task(
        id="task_001",
        title="Купить продукты",
        tags=["покупки", "дом"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=["msg1"],
        content="Купить молоко и хлеб"
    )


@pytest.fixture
def sample_note():
    """Тестовая заметка"""
    return Note(
        id="note_001",
        title="Идеи для проекта",
        tags=["идеи", "разработка"],
        created_at=datetime.now(),
        source_message_ids=["msg2"],
        content="Предложить использовать async/await"
    )


@pytest.fixture
def sample_messages():
    """Тестовые сообщения"""
    now = datetime.now()
    return [
        InboxMessage(
            id="msg1",
            from_user=123456789,
            sender_id=123456789,
            sender_name="Test User",
            content="Купить молоко",
            timestamp=now - timedelta(minutes=10),
            chat_id=123456789
        ),
        InboxMessage(
            id="msg2",
            from_user=123456789,
            sender_id=123456789,
            sender_name="Test User",
            content="Позвонить маме",
            timestamp=now - timedelta(minutes=5),
            chat_id=123456789
        )
    ]


@pytest.mark.asyncio
async def test_start_handler_with_data(mock_message, sample_task, sample_note):
    """Тест: /start со статистикой (задачи и заметки есть)"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task]
        fm_instance.read_notes.return_value = [sample_note]
        MockFM.return_value = fm_instance
        
        await start_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Notes Flow" in response
        assert "Задач создано: 1" in response
        assert "Заметок создано: 1" in response
        assert "Осталось задач: 1" in response
        assert "/inbox" in response
        assert "/tasks" in response
        assert "/notes" in response


@pytest.mark.asyncio
async def test_start_handler_empty(mock_message):
    """Тест: /start без данных (пустая статистика)"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = []
        fm_instance.read_notes.return_value = []
        MockFM.return_value = fm_instance
        
        await start_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Задач создано: 0" in response
        assert "Заметок создано: 0" in response
        assert "Осталось задач: 0" in response


@pytest.mark.asyncio
async def test_start_handler_error(mock_message):
    """Тест: /start с ошибкой"""
    with patch('handlers.commands.FileManager') as MockFM:
        MockFM.side_effect = Exception("Database error")
        
        await start_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ошибка" in response


@pytest.mark.asyncio
async def test_help_handler(mock_message):
    """Тест: /help показывает все команды"""
    with patch('handlers.commands.settings') as mock_settings:
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300  # 5 минут
        
        await help_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "/start" in response
        assert "/inbox" in response
        assert "/tasks" in response
        assert "/notes" in response
        assert "/summarize" in response
        assert "/settings" in response
        assert "/clear" in response
        assert "5 минут" in response


@pytest.mark.asyncio
async def test_summarize_handler(mock_message):
    """Тест: /summarize запускает саммаризацию"""
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await summarize_handler(mock_message)
        
        mock_summarize.assert_called_once_with(123456789)
        mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_inbox_handler_with_messages(mock_message, sample_messages):
    """Тест: /inbox с сообщениями"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_messages.return_value = sample_messages
        MockFM.return_value = fm_instance
        
        await inbox_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ваш инбокс" in response
        assert "Купить молоко" in response
        assert "Позвонить маме" in response


@pytest.mark.asyncio
async def test_inbox_handler_empty(mock_message):
    """Тест: /inbox пустой"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_messages.return_value = []
        MockFM.return_value = fm_instance
        
        await inbox_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Инбокс пуст" in response


@pytest.mark.asyncio
async def test_tasks_handler_with_tasks(mock_message, sample_task):
    """Тест: /tasks с задачами"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task]
        MockFM.return_value = fm_instance
        
        await tasks_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ваши задачи" in response
        assert "Купить продукты" in response
        assert "[покупки, дом]" in response


@pytest.mark.asyncio
async def test_tasks_handler_completed(mock_message, sample_task):
    """Тест: /tasks с выполненной задачей"""
    sample_task.status = "completed"
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task]
        MockFM.return_value = fm_instance
        
        await tasks_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "✅ Ваши задачи" in response


@pytest.mark.asyncio
async def test_tasks_handler_empty(mock_message):
    """Тест: /tasks без задач"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = []
        MockFM.return_value = fm_instance
        
        await tasks_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "пока нет задач" in response


@pytest.mark.asyncio
async def test_notes_handler_with_notes(mock_message, sample_note):
    """Тест: /notes с заметками"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = [sample_note]
        MockFM.return_value = fm_instance
        
        await notes_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ваши заметки" in response
        assert "Идеи для проекта" in response
        assert "[идеи, разработка]" in response


@pytest.mark.asyncio
async def test_notes_handler_empty(mock_message):
    """Тест: /notes без заметок"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = []
        MockFM.return_value = fm_instance
        
        await notes_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "пока нет заметок" in response


@pytest.mark.asyncio
async def test_clear_handler_inbox(mock_message):
    """Тест: /clear inbox очищает инбокс"""
    with patch('handlers.commands.summarizer_timer') as MockTimer, \
         patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.settings') as mock_settings:
        
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        MockTimer.reset = AsyncMock()
        fm_instance = MagicMock()
        MockFM.return_value = fm_instance
        
        mock_message.text = "/clear inbox"
        
        await clear_handler(mock_message)
        
        MockTimer.reset.assert_called_once_with(123456789)
        fm_instance.clear_messages.assert_called_once_with(123456789)
        mock_message.answer.assert_called_once()
        assert "Инбокс очищен" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_invalid(mock_message):
    """Тест: /settings с некорректными аргументами"""
    mock_message.text = "/settings delay abc"
    
    with patch('bot.config.settings') as mock_settings:
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "Некорректное значение" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_zero_delay(mock_message):
    """Тест: /settings delay 0 (минимальная задержка)"""
    with patch('bot.config.settings') as mock_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings delay 0"
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "должна быть не менее 1 минуты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_negative_delay(mock_message):
    """Тест: /settings delay с отрицательным значением"""
    with patch('bot.config.settings') as mock_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings delay -5"
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "должна быть не менее 1 минуты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_negative_delay(mock_message):
    """Тест: /settings delay с отрицательным значением"""
    with patch('bot.config.settings') as mock_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings delay -5"
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "должна быть не менее 1 минуты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_tasks_handler_multiple_tasks(mock_message, sample_task):
    """Тест: /tasks с несколькими задачами"""
    sample_task_2 = Task(
        id="task_002",
        title="Позвонить клиенту",
        tags=["работа", "звонки"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=["msg3"],
        content="Обсудить проект"
    )
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task, sample_task_2]
        MockFM.return_value = fm_instance
        
        await tasks_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ваши задачи" in response
        assert "Купить продукты" in response
        assert "Позвонить клиенту" in response


@pytest.mark.asyncio
async def test_notes_handler_multiple_notes(mock_message, sample_note):
    """Тест: /notes с несколькими заметками"""
    sample_note_2 = Note(
        id="note_002",
        title="Встреча с командой",
        tags=["встреча", "работа"],
        created_at=datetime.now(),
        source_message_ids=["msg4"],
        content="Обсудить прогресс проекта"
    )
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True):
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = [sample_note, sample_note_2]
        MockFM.return_value = fm_instance
        
        await notes_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        response = mock_message.answer.call_args[0][0]
        
        assert "Ваши заметки" in response
        assert "Идеи для проекта" in response
        assert "Встреча с командой" in response