import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from bot.db.models import InboxMessage, Task, Note
from handlers.commands import (
    start_handler,
    help_handler,
    settings_handler,
    inbox_handler,
    tasks_handler,
    notes_handler,
    clear_handler,
    done_task_handler,
    delete_task_handler,
    undone_task_handler,
    archive_handler,
    archive_date_handler,
    backup_handler
)

from handlers.commands import (
    update_or_create_task_message,
    update_or_create_archive_message,
    update_tasks_list
)
from handlers.summarizer import summarize_command


@pytest.fixture
def mock_message():
    """Mock Telegram message"""
    msg = AsyncMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock()
    msg.text = "/start"
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    msg.bot = AsyncMock()
    return msg


@pytest.fixture
def mock_message_with_update():
    """Mock Telegram message with update helpers"""
    msg = AsyncMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock()
    msg.answer.return_value = MagicMock(message_id=999)
    msg.text = "/tasks"
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    msg.bot = AsyncMock()
    msg.bot.edit_message_text = AsyncMock()
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
    with patch('bot.timers.manager.SummarizeTimer.trigger_immediate_summarization', new_callable=AsyncMock) as mock_trigger:
        mock_message.bot = MagicMock()
        mock_message.from_user.full_name = "Test User"
        
        await summarize_command(mock_message)
        
        mock_trigger.assert_called_once()
        call_args = mock_trigger.call_args
        assert call_args[1]['user_id'] == mock_message.from_user.id
        assert call_args[1]['user_name'] == "Test User"


@pytest.mark.asyncio
async def test_inbox_handler_with_messages(mock_message_with_update, sample_messages):
    """Тест: /inbox с сообщениями"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_archive_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_messages.return_value = sample_messages
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await inbox_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Ваш инбокс" in response
        assert "Купить молоко" in response
        assert "Позвонить маме" in response


@pytest.mark.asyncio
async def test_inbox_handler_empty(mock_message_with_update):
    """Тест: /inbox пустой"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_archive_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_messages.return_value = []
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await inbox_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Инбокс пуст" in response


@pytest.mark.asyncio
async def test_tasks_handler_with_tasks(mock_message_with_update, sample_task):
    """Тест: /tasks с задачами"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task]
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await tasks_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Ваши задачи" in response
        assert "Купить продукты" in response
        assert "[покупки, дом]" in response


@pytest.mark.asyncio
async def test_tasks_handler_completed(mock_message_with_update, sample_task):
    """Тест: /tasks с выполненной задачей"""
    sample_task.status = "completed"
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task]
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await tasks_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "✅ Ваши задачи" in response


@pytest.mark.asyncio
async def test_tasks_handler_empty(mock_message_with_update):
    """Тест: /tasks без задач"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = []
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await tasks_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "пока нет задач" in response


@pytest.mark.asyncio
async def test_notes_handler_with_notes(mock_message_with_update, sample_note):
    """Тест: /notes с заметками"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_archive_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = [sample_note]
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await notes_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Ваши заметки" in response
        assert "Идеи для проекта" in response
        assert "[идеи, разработка]" in response


@pytest.mark.asyncio
async def test_notes_handler_empty(mock_message_with_update):
    """Тест: /notes без заметок"""
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_archive_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = []
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await notes_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "пока нет заметок" in response


@pytest.mark.asyncio
async def test_clear_handler_inbox(mock_message_with_update):
    """Тест: /clear inbox очищает инбокс"""
    with patch('handlers.commands.summarizer_timer') as MockTimer, \
         patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.settings') as mock_settings, \
         patch('handlers.commands.update_tasks_list') as mock_update_tasks, \
         patch('handlers.commands.update_or_create_archive_message') as mock_update_archive:
        
        mock_settings.DEFAULT_SUMMARIZE_DELAY = 300
        MockTimer.reset = AsyncMock()
        fm_instance = MagicMock()
        MockFM.return_value = fm_instance
        mock_update_tasks.return_value = 999
        mock_update_archive.return_value = 999
        
        mock_message_with_update.text = "/clear inbox"
        
        await clear_handler(mock_message_with_update)
        
        MockTimer.reset.assert_called_once_with(123456789)
        fm_instance.clear_messages.assert_called_once_with(123456789)
        mock_message_with_update.answer.assert_called()
        mock_update_tasks.assert_called_once()
        mock_update_archive.assert_called_once()


@pytest.mark.asyncio
async def test_settings_handler_invalid(mock_message):
    """Тест: /settings с некорректными аргументами"""
    mock_message.text = "/settings delay abc"
    
    with patch('handlers.commands.user_settings') as mock_user_settings:
        mock_user_settings.get_user_delay.return_value = 300
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "Некорректное значение" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_short_form(mock_message):
    """Тест: /settings 10 (новый формат)"""
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_user_settings.get_user_delay.return_value = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings 10"
        
        await settings_handler(mock_message)
        
        mock_user_settings.set_delay.assert_called_once_with(123456789, 600)
        mock_message.answer.assert_called_once()
        assert "Задержка установлена на 10 минут" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_show_current(mock_message):
    """Тест: /settings (показать текущую задержку)"""
    with patch('handlers.commands.user_settings') as mock_user_settings:
        
        mock_user_settings.get_user_delay.return_value = 600
        
        mock_message.text = "/settings"
        
        await settings_handler(mock_message)
        
        mock_user_settings.get_user_delay.assert_called_once_with(123456789)
        mock_message.answer.assert_called_once()
        assert "Текущая задержка: 10 минут" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_old_format(mock_message):
    """Тест: /settings delay 15 (старый формат)"""
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_user_settings.get_user_delay.return_value = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings delay 15"
        
        await settings_handler(mock_message)
        
        mock_user_settings.set_delay.assert_called_once_with(123456789, 900)
        mock_message.answer.assert_called_once()
        assert "Задержка установлена на 15 минут" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_zero_delay(mock_message):
    """Тест: /settings 0 (минимальная задержка)"""
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_user_settings.get_user_delay.return_value = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings 0"
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "должна быть не менее 1 минуты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_handler_negative_delay(mock_message):
    """Тест: /settings с отрицательным значением"""
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_user_settings.get_user_delay.return_value = 300
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        mock_message.text = "/settings -5"
        
        await settings_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        assert "должна быть не менее 1 минуты" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_tasks_handler_multiple_tasks(mock_message_with_update, sample_task):
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
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_tasks.return_value = [sample_task, sample_task_2]
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await tasks_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Ваши задачи" in response
        assert "Купить продукты" in response
        assert "Позвонить клиенту" in response


@pytest.mark.asyncio
async def test_notes_handler_multiple_notes(mock_message_with_update, sample_note):
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
         patch('os.path.exists', return_value=True), \
         patch('handlers.commands.update_or_create_archive_message') as mock_update:
        fm_instance = MagicMock()
        fm_instance.read_notes.return_value = [sample_note, sample_note_2]
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await notes_handler(mock_message_with_update)
        
        mock_update.assert_called_once()
        response = mock_update.call_args[0][1]
        
        assert "Ваши заметки" in response
        assert "Идеи для проекта" in response
        assert "Встреча с командой" in response


@pytest.mark.asyncio
async def test_done_task_success(mock_message_with_update):
    """Тест команды /done_XXX"""
    mock_message_with_update.text = "/done_001"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.update_tasks_list') as mock_update:
        fm_instance = MagicMock()
        fm_instance.update_task_status.return_value = True
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await done_task_handler(mock_message_with_update)
        
        fm_instance.update_task_status.assert_called_once_with(123, "task_001", "completed")
        mock_message_with_update.answer.assert_called_once()
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_done_task_invalid_format(mock_message_with_update):
    """Тест команды с неверным форматом"""
    mock_message_with_update.text = "/done_abc"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        MockFM.return_value = MagicMock()
        mock_update.return_value = 999
        
        await done_task_handler(mock_message_with_update)
        
        MockFM.return_value.update_task_status.assert_not_called()
        # При неверном формате update_or_create_task_message не вызывается
        # Вместо этого вызывается обычный answer
        mock_message_with_update.answer.assert_called_once()
        assert "Неверный формат" in mock_message_with_update.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_done_task_not_found(mock_message_with_update):
    """Тест команды с несуществующей задачей"""
    mock_message_with_update.text = "/done_999"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.update_task_status.return_value = False
        MockFM.return_value = fm_instance
        
        await done_task_handler(mock_message_with_update)
        
        fm_instance.update_task_status.assert_called_once_with(123, "task_999", "completed")
        mock_message_with_update.answer.assert_called_once()


@pytest.mark.asyncio
async def test_delete_task_success(mock_message_with_update):
    """Тест команды /del_XXX"""
    mock_message_with_update.text = "/del_001"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.update_tasks_list') as mock_update:
        fm_instance = MagicMock()
        fm_instance.delete_task.return_value = True
        MockFM.return_value = fm_instance
        mock_update.return_value = 999
        
        await delete_task_handler(mock_message_with_update)
        
        fm_instance.delete_task.assert_called_once_with(123, "task_001")
        mock_message_with_update.answer.assert_called_once()
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_task_invalid_format(mock_message_with_update):
    """Тест команды с неверным форматом"""
    mock_message_with_update.text = "/del_abc"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM, \
         patch('handlers.commands.update_or_create_task_message') as mock_update:
        MockFM.return_value = MagicMock()
        mock_update.return_value = 999
        
        await delete_task_handler(mock_message_with_update)
        
        MockFM.return_value.delete_task.assert_not_called()
        # При неверном формате update_or_create_task_message не вызывается
        # Вместо этого вызывается обычный answer
        mock_message_with_update.answer.assert_called_once()
        assert "Неверный формат" in mock_message_with_update.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_delete_task_not_found(mock_message_with_update):
    """Тест команды с несуществующей задачей"""
    mock_message_with_update.text = "/del_999"
    mock_message_with_update.from_user.id = 123
    
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.delete_task.return_value = False
        MockFM.return_value = fm_instance
        
        await delete_task_handler(mock_message_with_update)
        
        fm_instance.delete_task.assert_called_once_with(123, "task_999")
        mock_message_with_update.answer.assert_called_once()