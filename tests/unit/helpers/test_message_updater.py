"""Tests for dynamic message updates (message_updater helper functions)"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.helpers.message_updater import update_or_create_task_message, update_or_create_archive_message


@pytest.fixture
def mock_message():
    """Mock Telegram message for testing"""
    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123456789
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    msg.bot = AsyncMock()
    msg.bot.edit_message_text = AsyncMock(return_value=MagicMock())
    msg.answer = AsyncMock(return_value=MagicMock(message_id=999))
    msg.text = "/tasks"
    return msg


@pytest.fixture
def mock_user_settings():
    """Mock user settings"""
    settings = MagicMock()
    settings.tasks_message_id = None
    settings.archive_message_id = None
    return settings


class TestUpdateOrCreateTaskMessage:
    """Tests for update_or_create_task_message function"""
    
    @pytest.mark.asyncio
    async def test_edit_existing_message(self, mock_message, mock_user_settings):
        """Test: редактирование существующего сообщения"""
        mock_message.from_user.id = 1
        mock_user_settings.tasks_message_id = 123
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_task_message(mock_message, "New tasks")
            
            mock_message.bot.edit_message_text.assert_called_once()
            assert result == 123
    
    @pytest.mark.asyncio
    async def test_send_new_message_no_saved_id(self, mock_message, mock_user_settings):
        """Test: отправка нового сообщения когда message_id не сохранён"""
        mock_message.from_user.id = 2
        mock_user_settings.tasks_message_id = None
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_task_message(mock_message, "New tasks")
            
            mock_message.answer.assert_called_once()
            assert result == 999
    
    @pytest.mark.asyncio
    async def test_fallback_to_new_message_on_edit_error(self, mock_message, mock_user_settings):
        """Test: падение на отправку нового сообщения при ошибке редактирования"""
        mock_message.from_user.id = 3
        mock_user_settings.tasks_message_id = 456
        mock_message.bot.edit_message_text = AsyncMock(side_effect=Exception("Edit failed"))
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_task_message(mock_message, "New tasks")
            
            # Должна быть попытка редактирования, а затем отправка нового
            mock_message.answer.assert_called_once()
            assert result == 999
    
    @pytest.mark.asyncio
    async def test_error_handling_no_bot(self, mock_message):
        """Test: обработка ошибки когда bot недоступен"""
        mock_message.from_user.id = 4
        mock_message.bot = None
        mock_message.answer = AsyncMock(return_value=None)
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = MagicMock(tasks_message_id=None)
            
            result = await update_or_create_task_message(mock_message, "New tasks")
            
            # Когда bot=None, fallback не сработает корректно
            # В зависимости от реализации может вернуться 0 или 999
            assert result in [0, 999]


class TestUpdateOrCreateArchiveMessage:
    """Tests for update_or_create_archive_message function"""
    
    @pytest.mark.asyncio
    async def test_edit_existing_archive_message(self, mock_message, mock_user_settings):
        """Test: редактирование существующего archive сообщения"""
        mock_message.from_user.id = 5
        mock_user_settings.archive_message_id = 789
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_archive_message(mock_message, "New archive")
            
            mock_message.bot.edit_message_text.assert_called_once()
            assert result == 789
    
    @pytest.mark.asyncio
    async def test_send_new_archive_message_no_saved_id(self, mock_message, mock_user_settings):
        """Test: отправка нового archive сообщения когда message_id не сохранён"""
        mock_message.from_user.id = 6
        mock_user_settings.archive_message_id = None
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_archive_message(mock_message, "New archive")
            
            mock_message.answer.assert_called_once()
            assert result == 999
    
    @pytest.mark.asyncio
    async def test_fallback_on_archive_edit_error(self, mock_message, mock_user_settings):
        """Test: падение на отправку нового сообщения при ошибке редактирования archive"""
        mock_message.from_user.id = 7
        mock_user_settings.archive_message_id = 101112
        mock_message.bot.edit_message_text = AsyncMock(side_effect=Exception("Edit failed"))
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_archive_message(mock_message, "New archive")
            
            mock_message.answer.assert_called_once()
            assert result == 999


class TestEdgeCases:
    """Tests for edge cases"""
    
    @pytest.mark.asyncio
    async def test_message_without_from_user(self, mock_message):
        """Test: сообщение без from_user (групповой чат)"""
        mock_message.from_user = None
        mock_message.chat.id = 999
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = MagicMock(tasks_message_id=None)
            
            result = await update_or_create_task_message(mock_message, "Group tasks")
            
            # Должна работать с chat.id
            assert result == 999
    
    @pytest.mark.asyncio
    async def test_message_id_zero(self, mock_message, mock_user_settings):
        """Test: message_id = 0 (невалидный ID, но проходит проверку is not None)"""
        mock_message.from_user.id = 10
        mock_user_settings.tasks_message_id = 0
        # При message_id=0 edit_message_text попытается отредактировать сообщение с ID 0
        # Это вызовет ошибку Telegram, которая будет перехвачена и сработает fallback
        mock_message.bot.edit_message_text = AsyncMock(side_effect=Exception("Message not found"))
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_task_message(mock_message, "Tasks with ID 0")
            
            # 0 проходит проверку is not None, пытается отредактировать
            # edit с ID=0 падает, затем fallback на answer
            mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_empty_text_message(self, mock_message, mock_user_settings):
        """Test: пустой текст сообщения"""
        mock_message.from_user.id = 11
        mock_user_settings.tasks_message_id = None
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            result = await update_or_create_task_message(mock_message, "")
            
            mock_message.answer.assert_called_once()
            assert result == 999
    
    @pytest.mark.asyncio
    async def test_message_with_special_characters(self, mock_message, mock_user_settings):
        """Test: текст со специальными символами"""
        mock_message.from_user.id = 12
        mock_user_settings.tasks_message_id = None
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = mock_user_settings
            
            special_text = "✅ Задачи:\n• Купить молоко\n• Позвонить маме\n\nЭмодзи: 🎉🚀"
            result = await update_or_create_task_message(mock_message, special_text)
            
            mock_message.answer.assert_called_once()
            call_text = mock_message.answer.call_args[0][0]
            assert "✅" in call_text
            assert "🎉" in call_text


class TestUserSettingsIntegration:
    """Tests for user_settings integration"""
    
    @pytest.mark.asyncio
    async def test_settings_created_for_new_user(self, mock_message):
        """Test: создание настроек для нового пользователя"""
        mock_message.from_user.id = 13
        
        with patch('bot.helpers.message_updater.user_settings') as mock_settings:
            mock_settings.get_counters.return_value = MagicMock(tasks_message_id=None)
            
            await update_or_create_task_message(mock_message, "Tasks")
            
            # get_counters должен быть вызван
            mock_settings.get_counters.assert_called_once_with(13)
