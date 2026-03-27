import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import time
from handlers.messages import restore_document_handler


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123456
    msg.answer = AsyncMock()
    msg.document = MagicMock()
    msg.document.file_name = "backup.zip"
    msg.document.file_id = "file_123"
    msg.bot = MagicMock()
    msg.bot.get_file = AsyncMock()
    msg.bot.download_file = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_restore_handler_valid_zip(mock_message):
    """Test restore handler with valid ZIP"""
    with patch('handlers.messages.FileManager') as MockFM, \
         patch('handlers.messages.os'):
        
        fm_instance = MagicMock()
        fm_instance.restore_from_backup.return_value = {
            'success': True,
            'message': 'Данные восстановлены'
        }
        MockFM.return_value = fm_instance
        
        mock_file = MagicMock()
        mock_file.file_path = "path/to/file"
        mock_message.bot.get_file.return_value = mock_file
        
        await restore_document_handler(mock_message)
        
        mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_restore_handler_non_zip_file(mock_message):
    """Test restore handler with non-ZIP file"""
    mock_message.document.file_name = "document.pdf"
    
    await restore_document_handler(mock_message)
    
    mock_message.answer.assert_called_with("Пожалуйста, загрузите ZIP-файл")
