"""
Tests for backup functionality in FileManager.

This module tests the create_backup() method including:
- ZIP file creation with various data scenarios
- File inclusion/exclusion logic
- Error cases (no user data, empty directories)
- ZIP structure validation
"""

import io
import json
import zipfile
from pathlib import Path
from datetime import datetime

import pytest

from bot.db.file_manager import FileManager
from bot.config.user_settings import SETTINGS_FILE


@pytest.fixture
def sample_user_id():
    """Sample user ID for tests"""
    return 123456789


@pytest.fixture
def file_manager(tmp_path):
    """Create FileManager instance with temp directory"""
    return FileManager(str(tmp_path))


@pytest.fixture
def user_data_dir(tmp_path, sample_user_id):
    """Create user data directory with sample files"""
    user_dir = tmp_path / str(sample_user_id)
    user_dir.mkdir()
    return user_dir


class TestCreateBackupBasic:
    """Tests for basic backup creation scenarios"""

    def test_create_backup_with_all_files(self, tmp_path, sample_user_id):
        """Test backup creation with all user files present"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ntimestamp: 2026-03-10T10:00:00\ncontent: Test message")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\ntitle: Test task\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test note")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        assert isinstance(result, io.BytesIO)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert 'tasks.md' in files
            assert 'notes.md' in files

    def test_create_backup_with_no_user_data(self, tmp_path, sample_user_id):
        """Test backup when user directory doesn't exist"""
        fm = FileManager(str(tmp_path))
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_create_backup_with_empty_user_directory(self, tmp_path, sample_user_id):
        """Test backup when user directory exists but is empty"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_create_backup_returns_bytesio(self, tmp_path, sample_user_id):
        """Test that backup returns BytesIO object"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("test")
        
        result = fm.create_backup(sample_user_id)
        
        assert isinstance(result, io.BytesIO)
        # BytesIO position should be at beginning after seek(0) in create_backup
        result.seek(0)
        assert result.tell() == 0

    def test_create_backup_zip_is_valid(self, tmp_path, sample_user_id):
        """Test that created ZIP file is valid and readable"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        
        try:
            with zipfile.ZipFile(result, 'r') as zf:
                zf.testzip()
        except zipfile.BadZipFile:
            pytest.fail("Created ZIP file is invalid")


class TestCreateBackupFileInclusion:
    """Tests for file inclusion logic in backups"""

    def test_includes_inbox_md(self, tmp_path, sample_user_id):
        """Test that inbox.md is included in backup"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            assert 'inbox.md' in zf.namelist()

    def test_includes_tasks_md(self, tmp_path, sample_user_id):
        """Test that tasks.md is included in backup"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\ntitle: Test")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            assert 'tasks.md' in zf.namelist()

    def test_includes_notes_md(self, tmp_path, sample_user_id):
        """Test that notes.md is included in backup"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            assert 'notes.md' in zf.namelist()

    def test_includes_archive_files(self, tmp_path, sample_user_id):
        """Test that files from archive/ directory are included"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10.md").write_text("---\ntype: archived_tasks\ntitle: Archive\n---\n\n## task_001\ntitle: Archived task")
        (archive_dir / "2026-03-11.md").write_text("---\ntype: archived_tasks\ntitle: Archive\n---\n\n## task_002\ntitle: Another archived task")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert 'archive/2026-03-10.md' in files
            assert 'archive/2026-03-11.md' in files

    def test_includes_inbox_backup_files(self, tmp_path, sample_user_id):
        """Test that files from inbox_backup/ directory are included"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        inbox_backup_dir = user_dir / "inbox_backup"
        inbox_backup_dir.mkdir()
        (inbox_backup_dir / "inbox_backup_20260310_120000.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Backup")
        (inbox_backup_dir / "inbox_backup_20260311_130000.md").write_text("---\ntype: inbox\n---\n\n## msg_002\ncontent: Backup 2")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert 'inbox_backup/inbox_backup_20260310_120000.md' in files
            assert 'inbox_backup/inbox_backup_20260311_130000.md' in files

    def test_excludes_user_settings_json(self, tmp_path, sample_user_id):
        """Test that user_settings.json is NOT included in backup"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "user_settings.json").write_text('{"123456789": {"delay": 300}}')
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'user_settings.json' not in files
            assert 'inbox.md' in files


class TestCreateBackupFileExclusion:
    """Tests for file exclusion logic"""

    def test_excludes_nonexistent_archive(self, tmp_path, sample_user_id):
        """Test that missing archive directory doesn't cause error"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert not any(f.startswith('archive/') for f in files)

    def test_excludes_nonexistent_inbox_backup(self, tmp_path, sample_user_id):
        """Test that missing inbox_backup directory doesn't cause error"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert not any(f.startswith('inbox_backup/') for f in files)

    def test_excludes_subdirectories_in_archive(self, tmp_path, sample_user_id):
        """Test that subdirectories in archive are not included"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "file.md").write_text("content")
        nested_dir = archive_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested_file.md").write_text("nested content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'archive/file.md' in files
            assert 'archive/nested' not in files
            assert 'archive/nested/nested_file.md' not in files


class TestCreateBackupErrorCases:
    """Tests for error handling and edge cases"""

    def test_error_no_user_data(self, tmp_path, sample_user_id):
        """Test error case when user data doesn't exist"""
        fm = FileManager(str(tmp_path))
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_error_empty_user_directory(self, tmp_path, sample_user_id):
        """Test error case when user directory is empty"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_error_only_settings_file(self, tmp_path, sample_user_id):
        """Test error case when only user_settings.json exists"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "user_settings.json").write_text('{"123456789": {"delay": 300}}')
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_error_with_only_empty_archive(self, tmp_path, sample_user_id):
        """Test case with only empty archive directory"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None

    def test_error_with_only_empty_inbox_backup(self, tmp_path, sample_user_id):
        """Test case with only empty inbox_backup directory"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        inbox_backup_dir = user_dir / "inbox_backup"
        inbox_backup_dir.mkdir()
        
        result = fm.create_backup(sample_user_id)
        
        assert result is None


class TestCreateBackupZipStructure:
    """Tests for ZIP file structure validation"""

    def test_zip_contains_expected_files(self, tmp_path, sample_user_id):
        """Test ZIP contains exactly the expected files"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\ntitle: Test")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10.md").write_text("archive content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = set(zf.namelist())
            expected = {'inbox.md', 'tasks.md', 'notes.md', 'archive/2026-03-10.md'}
            assert files == expected

    def test_zip_file_paths_are_correct(self, tmp_path, sample_user_id):
        """Test that file paths in ZIP are correct"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("content")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "test.md").write_text("content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert 'archive/test.md' in files
            assert not any(f.startswith('/') for f in files)
            assert not any(f.startswith('../') for f in files)

    def test_zip_contains_file_contents(self, tmp_path, sample_user_id):
        """Test that ZIP contains actual file contents"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test message content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            content = zf.read('inbox.md').decode('utf-8')
            assert 'Test message content' in content
            assert 'type: inbox' in content

    def test_zip_handles_special_characters_in_filenames(self, tmp_path, sample_user_id):
        """Test ZIP creation with special characters in filenames"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10_special-file.md").write_text("content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'archive/2026-03-10_special-file.md' in files

    def test_zip_handles_unicode_in_filenames(self, tmp_path, sample_user_id):
        """Test ZIP creation with unicode characters in filenames"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "архив_2026-03-10.md").write_text("content")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'archive/архив_2026-03-10.md' in files

    def test_zip_handles_multiple_archive_files(self, tmp_path, sample_user_id):
        """Test ZIP creation with multiple archive files"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        for i in range(10):
            (archive_dir / f"2026-03-{i:02d}.md").write_text(f"archive {i}")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert len([f for f in files if f.startswith('archive/')]) == 10

    def test_zip_handles_multiple_inbox_backup_files(self, tmp_path, sample_user_id):
        """Test ZIP creation with multiple inbox backup files"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        inbox_backup_dir = user_dir / "inbox_backup"
        inbox_backup_dir.mkdir()
        for i in range(5):
            filename = f"inbox_backup_20260310_{12+i:02d}00.md"
            (inbox_backup_dir / filename).write_text(f"backup {i}")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert 'inbox.md' in files
            assert len([f for f in files if f.startswith('inbox_backup/')]) == 5


class TestCreateBackupEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_backup_with_only_inbox(self, tmp_path, sample_user_id):
        """Test backup with only inbox.md file"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert files == ['inbox.md']

    def test_backup_with_only_tasks(self, tmp_path, sample_user_id):
        """Test backup with only tasks.md file"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\ntitle: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert files == ['tasks.md']

    def test_backup_with_only_notes(self, tmp_path, sample_user_id):
        """Test backup with only notes.md file"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            assert files == ['notes.md']

    def test_backup_with_large_files(self, tmp_path, sample_user_id):
        """Test backup with larger files"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        large_content = "---\ntype: inbox\n---\n\n"
        for i in range(1000):
            large_content += f"## msg_{i:04d}\ncontent: Message number {i}\n\n"
        
        (user_dir / "inbox.md").write_text(large_content)
        
        result = fm.create_backup(sample_user_id)
        
        assert result is not None
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            content = zf.read('inbox.md').decode('utf-8')
            assert 'Message number 999' in content

    def test_backup_different_users_independent(self, tmp_path):
        """Test that backups for different users are independent"""
        fm = FileManager(str(tmp_path))
        
        user1_dir = tmp_path / "111111111"
        user1_dir.mkdir()
        (user1_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: User 1")
        
        user2_dir = tmp_path / "222222222"
        user2_dir.mkdir()
        (user2_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: User 2")
        
        backup1 = fm.create_backup(111111111)
        backup2 = fm.create_backup(222222222)
        
        assert backup1 is not None
        assert backup2 is not None
        
        backup1.seek(0)
        with zipfile.ZipFile(backup1, 'r') as zf:
            content1 = zf.read('inbox.md').decode('utf-8')
            assert 'User 1' in content1
            assert 'User 2' not in content1
        
        backup2.seek(0)
        with zipfile.ZipFile(backup2, 'r') as zf:
            content2 = zf.read('inbox.md').decode('utf-8')
            assert 'User 2' in content2
            assert 'User 1' not in content2

    def test_backup_preserves_file_structure(self, tmp_path, sample_user_id):
        """Test that backup preserves directory structure"""
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10.md").write_text("archive")
        
        inbox_backup_dir = user_dir / "inbox_backup"
        inbox_backup_dir.mkdir()
        (inbox_backup_dir / "inbox_backup_20260310_120000.md").write_text("inbox backup")
        
        result = fm.create_backup(sample_user_id)
        
        result.seek(0)
        with zipfile.ZipFile(result, 'r') as zf:
            files = zf.namelist()
            
            assert 'inbox.md' in files
            assert 'archive/2026-03-10.md' in files
            assert 'inbox_backup/inbox_backup_20260310_120000.md' in files
            
            assert not any(f.startswith('/') for f in files)
            assert not any('..' in f for f in files)


class TestRestoreFromBackup:

    def test_restore_from_valid_backup(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Original inbox")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: completed")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Original note")
        
        backup = fm.create_backup(sample_user_id)
        assert backup is not None
        
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Modified inbox")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Modified note")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result
        assert 'message' in result
        
        restored_inbox = (user_dir / "inbox.md").read_text()
        assert "Original inbox" in restored_inbox
        assert "Modified inbox" not in restored_inbox
        
        restored_tasks = (user_dir / "tasks.md").read_text()
        assert "completed" in restored_tasks
        assert "pending" not in restored_tasks
        
        restored_notes = (user_dir / "notes.md").read_text()
        assert "Original note" in restored_notes
        assert "Modified note" not in restored_notes

    def test_restore_from_backup_file_not_found(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        result = fm.restore_from_backup(sample_user_id, str(tmp_path / "nonexistent.zip"))
        
        assert result['success'] is False
        assert 'error' in result
        assert 'not found' in result['error'].lower()

    def test_restore_from_backup_not_a_file(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_dir = tmp_path / "backup_dir"
        backup_dir.mkdir()
        
        result = fm.restore_from_backup(sample_user_id, str(backup_dir))
        
        assert result['success'] is False
        assert 'error' in result
        assert 'not a file' in result['error'].lower()

    def test_restore_from_backup_empty_zip(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            pass
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is False
        assert 'error' in result
        assert 'empty' in result['error'].lower()

    def test_restore_from_backup_invalid_zip(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "invalid.zip"
        backup_path.write_text("This is not a ZIP file")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is False
        assert 'error' in result
        assert 'invalid' in result['error'].lower() or 'badzip' in result['error'].lower()

    def test_restore_from_backup_missing_required_files(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "incomplete.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is False
        assert 'error' in result
        assert 'missing' in result['error'].lower()
        assert 'tasks.md' in result['error'] or 'notes.md' in result['error']

    def test_restore_from_backup_with_archive(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10.md").write_text("---\ntype: archived_tasks\n---\n\n## task_archived\nstatus: completed")
        
        backup = fm.create_backup(sample_user_id)
        assert backup is not None
        
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'archive/*' in result['files_restored']
        
        restored_archive = user_dir / "archive" / "2026-03-10.md"
        assert restored_archive.exists()
        assert "task_archived" in restored_archive.read_text()

    def test_restore_from_backup_with_inbox_backup(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        inbox_backup_dir = user_dir / "inbox_backup"
        inbox_backup_dir.mkdir()
        (inbox_backup_dir / "inbox_backup_20260310_120000.md").write_text("---\ntype: inbox\n---\n\n## msg_backup\ncontent: Backup")
        
        backup = fm.create_backup(sample_user_id)
        assert backup is not None
        
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'inbox_backup/*' in result['files_restored']
        
        restored_backup = inbox_backup_dir / "inbox_backup_20260310_120000.md"
        assert restored_backup.exists()
        assert "Backup" in restored_backup.read_text()


class TestRestoreRollback:

    def test_pre_restore_backup_created(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        backup = fm.create_backup(sample_user_id)
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'pre_restore_backup' in result
    
    def test_pre_restore_backup_with_settings_file(self, tmp_path, sample_user_id):
        import os
        os.chdir(str(tmp_path))
        
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        settings_dir = tmp_path / "data"
        settings_dir.mkdir()
        settings_path = settings_dir / "user_settings.json"
        settings_path.write_text(json.dumps({str(sample_user_id): {"delay": 600}}))
        
        backup = fm.create_backup(sample_user_id)
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        (settings_path).write_text(json.dumps({str(sample_user_id): {"delay": 300}}))
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        
        pre_restore_path = Path(result['pre_restore_backup'])
        assert pre_restore_path.exists()
        
        restored_settings = json.loads(pre_restore_path.read_text())
        assert str(sample_user_id) in restored_settings
        assert restored_settings[str(sample_user_id)]['delay'] == 300
        
        os.chdir("/")
    
    def test_pre_restore_backup_not_created_when_no_settings(self, tmp_path, sample_user_id):
        import os
        os.chdir(str(tmp_path))
        
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        backup = fm.create_backup(sample_user_id)
        backup_path = tmp_path / "backup.zip"
        backup_path.write_bytes(backup.getvalue())
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'pre_restore_backup' in result
        
        os.chdir("/")


class TestRestoreValidationErrors:

    def test_restore_invalid_yaml_in_inbox(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "invalid_yaml.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: [invalid yaml")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result

    def test_restore_corrupted_file_content(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "corrupted.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result

    def test_restore_missing_timestamp(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        backup_path = tmp_path / "missing_timestamp.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test without timestamp")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result


class TestRestoreUserSettings:

    def test_restore_settings_for_same_user(self, tmp_path, sample_user_id):
        import os
        os.chdir(str(tmp_path))
        
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        settings_data = {
            str(sample_user_id): {"delay": 600},
            "999999999": {"delay": 1200}
        }
        
        backup_path = tmp_path / "with_settings.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
            zf.writestr("user_settings.json", json.dumps(settings_data))
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        
        settings_path = tmp_path / "data" / "user_settings.json"
        assert settings_path.exists()
        
        restored_settings = json.loads(settings_path.read_text())
        assert str(sample_user_id) in restored_settings
        assert restored_settings[str(sample_user_id)] == 600
        
        os.chdir("/")

    def test_restore_settings_invalid_delay(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        settings_data = {
            str(sample_user_id): {"delay": -100},
        }
        
        backup_path = tmp_path / "invalid_delay.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
            zf.writestr("user_settings.json", json.dumps(settings_data))
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True

    def test_restore_settings_invalid_json(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        backup_path = tmp_path / "invalid_json.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
            zf.writestr("user_settings.json", "this is not valid json {{{")
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result

    def test_restore_settings_not_dict(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        backup_path = tmp_path / "not_dict.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
            zf.writestr("user_settings.json", json.dumps(["invalid", "format"]))
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result

    def test_restore_settings_missing_user_key(self, tmp_path, sample_user_id):
        fm = FileManager(str(tmp_path))
        
        user_dir = tmp_path / str(sample_user_id)
        user_dir.mkdir()
        
        (user_dir / "inbox.md").write_text("---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
        (user_dir / "tasks.md").write_text("---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
        (user_dir / "notes.md").write_text("---\ntype: notes\n---\n\n## note_001\ntitle: Test")
        
        settings_data = {
            "999999999": {"delay": 600}
        }
        
        backup_path = tmp_path / "missing_user_key.zip"
        with zipfile.ZipFile(backup_path, 'w') as zf:
            zf.writestr("inbox.md", "---\ntype: inbox\n---\n\n## msg_001\ncontent: Test")
            zf.writestr("tasks.md", "---\ntype: tasks\n---\n\n## task_001\nstatus: pending")
            zf.writestr("notes.md", "---\ntype: notes\n---\n\n## note_001\ntitle: Test")
            zf.writestr("user_settings.json", json.dumps(settings_data))
        
        result = fm.restore_from_backup(sample_user_id, str(backup_path))
        
        assert result['success'] is True
        assert 'files_restored' in result
