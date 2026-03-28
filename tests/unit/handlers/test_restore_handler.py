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


@pytest.fixture
def mock_state():
    state = MagicMock()
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


@pytest.mark.asyncio
async def test_restore_handler_valid_zip(mock_message, mock_state):
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
        
        await restore_document_handler(mock_message, mock_state)
        
        mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_restore_handler_non_zip_file(mock_message, mock_state):
    """Test restore handler with non-ZIP file"""
    mock_message.document.file_name = "document.pdf"
    
    await restore_document_handler(mock_message, mock_state)
    
    mock_message.answer.assert_called_with("Пожалуйста, загрузите ZIP-файл")


@pytest.mark.asyncio
async def test_restore_handler_missing_files(mock_message, mock_state):
    """Test restore handler when backup is missing required files"""
    with patch('handlers.messages.FileManager') as MockFM, \
         patch('handlers.messages.os'):
        
        fm_instance = MagicMock()
        fm_instance.restore_from_backup.return_value = {
            'success': True,
            'files_restored': [],
            'message': 'Backup preview: 2 files found',
            'missing_files': ['inbox.md', 'tasks.md'],
            'files_available': ['notes.md'],
            'pre_restore_backup': None,
            'temp_dir': '/tmp/restore_123'
        }
        MockFM.return_value = fm_instance
        
        mock_file = MagicMock()
        mock_file.file_path = "path/to/file"
        mock_message.bot.get_file.return_value = mock_file
        
        await restore_document_handler(mock_message, mock_state)
        
        # Should show preview with confirmation buttons
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert 'Предварительный просмотр бэкапа' in call_args
        assert 'inbox.md' in call_args
        assert 'tasks.md' in call_args
        assert 'notes.md' in call_args
        
        # Should store temp_dir in state
        mock_state.update_data.assert_called()
        mock_state.set_state.assert_called()
