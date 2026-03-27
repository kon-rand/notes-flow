import sys
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import pytest
import shutil
import zipfile
import io
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage, Task, Note


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
def sample_user_data(clean_data_dir):
    """Create sample user data for testing backup/restore"""
    user_id = 123456789
    fm = FileManager()
    
    # Create inbox messages
    messages = [
        InboxMessage(
            id="msg_001",
            timestamp=datetime(2026, 3, 6, 14, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test User",
            content="Нужно подготовить отчёт по проекту",
            chat_id=-1001234567890
        ),
        InboxMessage(
            id="msg_002",
            timestamp=datetime(2026, 3, 6, 14, 5, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test User",
            content="Вот данные для отчёта: [ссылка на файл]",
            chat_id=-1001234567890
        ),
    ]
    for msg in messages:
        fm.append_message(user_id, msg)
    
    # Create task
    fm.append_task(user_id, Task(
        id="task_001",
        title="Подготовить отчёт",
        tags=["работа", "отчёт"],
        content="Собрать данные и написать отчёт",
        status="pending",
        created_at=datetime(2026, 3, 6, 14, 10, 0),
        source_message_ids=["msg_001"]
    ))
    
    # Create note
    fm.append_note(user_id, Note(
        id="note_001",
        title="Идеи для проекта",
        tags=["проект"],
        created_at=datetime(2026, 3, 6, 14, 15, 0),
        source_message_ids=[],
        content="Важные идеи для проекта"
    ))
    
    return user_id, fm


class TestBackupRestoreIntegration:
    """Integration tests for backup and restore functionality"""
    
    def test_create_backup_with_data(self, clean_data_dir, sample_user_data):
        """Test: create backup when user has data -> returns valid ZIP file"""
        user_id, fm = sample_user_data
        
        backup_file = fm.create_backup(user_id)
        
        assert backup_file is not None
        assert isinstance(backup_file, io.BytesIO)
        
        backup_file.seek(0)
        with zipfile.ZipFile(backup_file, 'r') as zip_file:
            file_list = zip_file.namelist()
            assert 'inbox.md' in file_list
            assert 'tasks.md' in file_list
            assert 'notes.md' in file_list
    
    def test_create_backup_empty_user(self, clean_data_dir):
        """Test: create backup for user with no data -> returns None"""
        fm = FileManager()
        
        backup_file = fm.create_backup(999999)
        
        assert backup_file is None
    
    def test_create_backup_no_user_directory(self, clean_data_dir):
        """Test: create backup when user directory doesn't exist -> returns None"""
        fm = FileManager()
        
        backup_file = fm.create_backup(888888)
        
        assert backup_file is None
    
    def test_restore_from_backup_success(self, clean_data_dir, sample_user_data):
        """Test: restore from backup -> data restored successfully"""
        user_id, original_fm = sample_user_data
        
        backup_file = original_fm.create_backup(user_id)
        assert backup_file is not None
        
        backup_path = "/tmp/test_backup.zip"
        backup_file.seek(0)
        with open(backup_path, 'wb') as f:
            f.write(backup_file.read())
        
        original_dir = Path("data") / str(user_id)
        shutil.rmtree(original_dir)
        
        restored_fm = FileManager()
        result = restored_fm.restore_from_backup(user_id, backup_path)
        
        assert result['success'] is True
        assert 'files_restored' in result
        assert 'inbox.md' in result['files_restored']
        assert 'tasks.md' in result['files_restored']
        assert 'notes.md' in result['files_restored']
        
        restored_messages = restored_fm.read_messages(user_id)
        assert len(restored_messages) == 2
        
        restored_tasks = restored_fm.read_tasks(user_id)
        assert len(restored_tasks) == 1
        assert restored_tasks[0].title == "Подготовить отчёт"
        
        restored_notes = restored_fm.read_notes(user_id)
        assert len(restored_notes) == 1
        assert restored_notes[0].title == "Идеи для проекта"
        
        os.remove(backup_path)
    
    def test_restore_from_backup_invalid_file(self, clean_data_dir):
        """Test: restore from invalid ZIP file -> returns error"""
        fm = FileManager()
        
        invalid_zip_path = "/tmp/invalid_backup.zip"
        with open(invalid_zip_path, 'wb') as f:
            f.write(b"This is not a valid ZIP file")
        
        result = fm.restore_from_backup(123456, invalid_zip_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Invalid ZIP' in result['error']
        
        os.remove(invalid_zip_path)
    
    def test_restore_from_backup_file_not_found(self, clean_data_dir):
        """Test: restore from non-existent file -> returns error"""
        fm = FileManager()
        
        result = fm.restore_from_backup(123456, "/tmp/nonexistent.zip")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'not found' in result['error'].lower()
    
    def test_restore_from_backup_empty_zip(self, clean_data_dir):
        """Test: restore from empty ZIP file -> returns error"""
        fm = FileManager()
        
        empty_zip_path = "/tmp/empty_backup.zip"
        with zipfile.ZipFile(empty_zip_path, 'w') as zip_file:
            pass
        
        result = fm.restore_from_backup(123456, empty_zip_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'empty' in result['error'].lower()
        
        os.remove(empty_zip_path)
    
    def test_restore_from_backup_missing_required_files(self, clean_data_dir):
        """Test: restore from ZIP missing required files -> returns error"""
        fm = FileManager()
        
        incomplete_zip_path = "/tmp/incomplete_backup.zip"
        with zipfile.ZipFile(incomplete_zip_path, 'w') as zip_file:
            inbox_content = """---
type: inbox
---

## msg_001
timestamp: 2026-03-06T14:00:00
from_user: 123456789
sender_id: 123456789
sender_name: Test
content: Test message
chat_id: -1001234567890
"""
            zip_file.writestr("inbox.md", inbox_content)
        
        result = fm.restore_from_backup(123456, incomplete_zip_path)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'missing' in result['error'].lower() or 'required' in result['error'].lower()
        
        os.remove(incomplete_zip_path)
    
    def test_backup_restore_preserves_archive_data(self, clean_data_dir, sample_user_data):
        """Test: backup includes archive files -> archive restored correctly"""
        user_id, original_fm = sample_user_data
        
        archive_dir = Path("data") / str(user_id) / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archive_content = """---
type: task_archive
archived_date: 2026-03-05
---

## task_002
title: Выполненная задача
tags: [работа]
status: completed
created_at: 2026-03-05T10:00:00
archived_at: 2026-03-06T00:00:00
content: Старая задача
"""
        with open(archive_dir / "2026-03-05.md", 'w', encoding='utf-8') as f:
            f.write(archive_content)
        
        backup_file = original_fm.create_backup(user_id)
        assert backup_file is not None
        
        backup_path = "/tmp/test_backup_with_archive.zip"
        backup_file.seek(0)
        with open(backup_path, 'wb') as f:
            f.write(backup_file.read())
        
        original_dir = Path("data") / str(user_id)
        shutil.rmtree(original_dir)
        
        restored_fm = FileManager()
        result = restored_fm.restore_from_backup(user_id, backup_path)
        
        assert result['success'] is True
        
        restored_archive_dir = Path("data") / str(user_id) / "archive"
        assert restored_archive_dir.exists()
        assert (restored_archive_dir / "2026-03-05.md").exists()
        
        os.remove(backup_path)
    
    def test_backup_restore_preserves_inbox_backup_data(self, clean_data_dir, sample_user_data):
        """Test: backup includes inbox_backup files -> inbox_backup restored correctly"""
        user_id, original_fm = sample_user_data
        
        inbox_backup_dir = Path("data") / str(user_id) / "inbox_backup"
        inbox_backup_dir.mkdir(parents=True, exist_ok=True)
        
        inbox_backup_content = """---
type: inbox
---

## inbox_msg_001
timestamp: 2026-03-05T10:00:00
from_user: 123456789
sender_id: 123456789
sender_name: Test
content: Входящее сообщение
chat_id: -1001234567890
"""
        with open(inbox_backup_dir / "inbox_backup_20260305_100000.md", 'w', encoding='utf-8') as f:
            f.write(inbox_backup_content)
        
        backup_file = original_fm.create_backup(user_id)
        assert backup_file is not None
        
        backup_path = "/tmp/test_backup_with_inbox_backup.zip"
        backup_file.seek(0)
        with open(backup_path, 'wb') as f:
            f.write(backup_file.read())
        
        original_dir = Path("data") / str(user_id)
        shutil.rmtree(original_dir)
        
        restored_fm = FileManager()
        result = restored_fm.restore_from_backup(user_id, backup_path)
        
        assert result['success'] is True
        
        restored_inbox_backup_dir = Path("data") / str(user_id) / "inbox_backup"
        assert restored_inbox_backup_dir.exists()
        assert (restored_inbox_backup_dir / "inbox_backup_20260305_100000.md").exists()
        
        os.remove(backup_path)
    
    def test_restore_user_data_with_existing_data(self, clean_data_dir, sample_user_data):
        """Test: restore when user already has data -> original data preserved as backup"""
        user_id, original_fm = sample_user_data
        
        backup_file = original_fm.create_backup(user_id)
        backup_path = "/tmp/test_restore_with_existing.zip"
        backup_file.seek(0)
        with open(backup_path, 'wb') as f:
            f.write(backup_file.read())
        
        new_fm = FileManager()
        new_fm.append_message(user_id, InboxMessage(
            id="msg_003",
            timestamp=datetime(2026, 3, 7, 10, 0, 0),
            from_user=user_id,
            sender_id=user_id,
            sender_name="Test User",
            content="Новое сообщение после бэкапа",
            chat_id=-1001234567890
        ))
        
        result = new_fm.restore_from_backup(user_id, backup_path)
        
        assert result['success'] is True
        
        restored_messages = new_fm.read_messages(user_id)
        assert len(restored_messages) == 2
        
        os.remove(backup_path)


class TestBackupRestoreCommandIntegration:
    """Integration tests for backup and restore commands"""
    
    @pytest.mark.asyncio
    async def test_backup_handler_creates_and_sends_backup(self, clean_data_dir, sample_user_data):
        """Test: /backup command -> creates backup and sends as document"""
        from handlers.commands import backup_handler
        from aiogram.types import Message, User
        from io import BytesIO
        
        user_id, fm = sample_user_data
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = User(id=user_id, first_name="Test", is_bot=False)
        mock_message.text = "/backup"
        mock_message.answer = AsyncMock()
        mock_message.answer_document = AsyncMock()
        
        mock_bot = AsyncMock()
        mock_message.bot = mock_bot
        
        with patch('handlers.commands.InputFile') as MockInputFile:
            mock_input_file = MagicMock()
            mock_input_file.read = MagicMock(return_value=b"fake backup data")
            MockInputFile.return_value = mock_input_file
            
            await backup_handler(mock_message)
        
        mock_message.answer_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backup_handler_no_data(self, clean_data_dir):
        """Test: /backup command with no user data -> sends error message"""
        from handlers.commands import backup_handler
        from aiogram.types import Message, User
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = User(id=999999, first_name="Test", is_bot=False)
        mock_message.text = "/backup"
        mock_message.answer = AsyncMock()
        mock_message.answer_document = AsyncMock()
        
        mock_bot = AsyncMock()
        mock_message.bot = mock_bot
        
        await backup_handler(mock_message)
        
        mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backup_handler_no_user(self, clean_data_dir):
        """Test: /backup command with no from_user -> returns early"""
        from handlers.commands import backup_handler
        from aiogram.types import Message
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None
        mock_message.text = "/backup"
        mock_message.answer = AsyncMock()
        mock_message.answer_document = AsyncMock()
        
        await backup_handler(mock_message)
        
        mock_message.answer.assert_not_called()
        mock_message.answer_document.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_restore_document_handler_valid_zip(self, clean_data_dir, sample_user_data):
        """Test: restore document handler with valid ZIP -> restores data"""
        from handlers.messages import restore_document_handler
        from aiogram.types import Message, User, Document, File
        import time
        
        user_id, fm = sample_user_data
        
        backup_file = fm.create_backup(user_id)
        backup_path = "/tmp/restore_test_valid.zip"
        backup_file.seek(0)
        with open(backup_path, 'wb') as f:
            f.write(backup_file.read())
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = User(id=user_id, first_name="Test", is_bot=False)
        mock_message.answer = AsyncMock()
        
        mock_document = AsyncMock(spec=Document)
        mock_document.file_name = "backup.zip"
        mock_document.file_id = "file_123"
        mock_message.document = mock_document
        
        mock_bot = AsyncMock()
        mock_file = AsyncMock(spec=File)
        mock_file.file_path = backup_path
        mock_bot.get_file = AsyncMock(return_value=mock_file)
        async def mock_download_file(file_path, dest_path):
            shutil.copy2(backup_path, dest_path)
        mock_bot.download_file = AsyncMock(side_effect=mock_download_file)
        mock_message.bot = mock_bot
        
        await restore_document_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert 'restored' in call_args.args[0].lower()
        
        restored_fm = FileManager()
        restored_messages = restored_fm.read_messages(user_id)
        assert len(restored_messages) == 2
        
        os.remove(backup_path)
    
    @pytest.mark.asyncio
    async def test_restore_document_handler_not_zip(self, clean_data_dir):
        """Test: restore document handler with non-ZIP file -> sends error"""
        from handlers.messages import restore_document_handler
        from aiogram.types import Message, User, Document
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = User(id=123456, first_name="Test", is_bot=False)
        mock_message.answer = AsyncMock()
        
        mock_document = AsyncMock(spec=Document)
        mock_document.file_name = "document.pdf"
        mock_message.document = mock_document
        
        mock_bot = AsyncMock()
        mock_message.bot = mock_bot
        
        await restore_document_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert 'ZIP' in call_args.args[0]
    
    @pytest.mark.asyncio
    async def test_restore_document_handler_no_user(self, clean_data_dir):
        """Test: restore document handler with no from_user -> returns early"""
        from handlers.messages import restore_document_handler
        from aiogram.types import Message
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None
        mock_message.document = None
        
        await restore_document_handler(mock_message)
        
        mock_message.answer.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_restore_document_handler_restore_error(self, clean_data_dir):
        """Test: restore document handler with restore failure -> sends error message"""
        from handlers.messages import restore_document_handler
        from aiogram.types import Message, User, Document, File
        
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = User(id=123456, first_name="Test", is_bot=False)
        mock_message.answer = AsyncMock()
        
        mock_document = AsyncMock(spec=Document)
        mock_document.file_name = "invalid.zip"
        mock_document.file_id = "file_456"
        mock_message.document = mock_document
        
        mock_bot = AsyncMock()
        mock_file = AsyncMock(spec=File)
        mock_file.file_path = "/tmp/invalid.zip"
        mock_bot.get_file = AsyncMock(return_value=mock_file)
        mock_bot.download_file = AsyncMock(return_value=None)
        mock_message.bot = mock_bot
        
        with open("/tmp/invalid.zip", 'wb') as f:
            f.write(b"Not a valid ZIP")
        
        await restore_document_handler(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert '❌' in call_args.args[0] or 'error' in call_args.args[0].lower()
        
        os.remove("/tmp/invalid.zip")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
