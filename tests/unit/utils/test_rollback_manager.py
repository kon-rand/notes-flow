import sys
import pytest
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

from pathlib import Path
from utils.rollback_manager import RollbackManager, RollbackError


@pytest.fixture
def user_data_setup(tmp_path):
    """Setup user data directory with initial files"""
    user_dir = tmp_path / "123456"
    user_dir.mkdir()
    
    (user_dir / "inbox.md").write_text("original content")
    (user_dir / "tasks.md").write_text("original tasks")
    (user_dir / "notes.md").write_text("original notes")
    
    return tmp_path


def test_create_backup(tmp_path, user_data_setup):
    """Test backup creation"""
    rm = RollbackManager(123456, str(tmp_path))
    result = rm.create_backup()
    assert result is True
    assert rm.backup_path.exists()


def test_rollback(tmp_path, user_data_setup):
    """Test rollback restores data"""
    rm = RollbackManager(123456, str(tmp_path))
    rm.create_backup()
    
    # Modify data
    (tmp_path / "123456" / "inbox.md").write_text("modified")
    
    # Rollback
    result = rm.rollback()
    assert result is True
    
    # Verify restoration
    content = (tmp_path / "123456" / "inbox.md").read_text()
    assert content == "original content"


def test_cleanup(tmp_path, user_data_setup):
    """Test backup cleanup"""
    rm = RollbackManager(123456, str(tmp_path))
    rm.create_backup()
    result = rm.cleanup()
    assert result is True
    assert not rm.backup_path.exists()


def test_rollback_without_backup(tmp_path):
    """Test rollback without backup raises error"""
    rm = RollbackManager(123456, str(tmp_path))
    with pytest.raises(RollbackError):
        rm.rollback()
