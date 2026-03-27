import io
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from aiogram.types import Message
from handlers.commands import backup_handler


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123456
    msg.answer = AsyncMock()
    msg.answer_document = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_backup_handler_with_data(mock_message):
    """Test backup handler with user data"""
    with patch('handlers.commands.FileManager') as MockFM:
        with patch('handlers.commands.InputFile') as MockInputFile:
            fm_instance = MagicMock()
            backup_file = io.BytesIO(b"zip_data")
            fm_instance.create_backup.return_value = backup_file
            MockFM.return_value = fm_instance
            
            await backup_handler(mock_message)
            
            mock_message.answer_document.assert_called_once()
            MockInputFile.assert_called_once()


@pytest.mark.asyncio
async def test_backup_handler_no_data(mock_message):
    """Test backup handler with no user data"""
    with patch('handlers.commands.FileManager') as MockFM:
        fm_instance = MagicMock()
        fm_instance.create_backup.return_value = None
        MockFM.return_value = fm_instance
        
        await backup_handler(mock_message)
        
        mock_message.answer.assert_called_with("Нет данных для бэкапа")
