import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from bot.db.backup_state import BackupState, BackupStateManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_manager(temp_dir):
    state_file = Path(temp_dir) / "backup_state.json"
    return BackupStateManager(str(state_file))


class TestBackupState:
    def test_create_backup_state(self):
        timestamp = datetime(2026, 3, 28, 2, 0, 0)
        state = BackupState(user_id=123, last_backup_timestamp=timestamp, last_backup_hash="abc123")
        
        assert state.user_id == 123
        assert state.last_backup_timestamp == timestamp
        assert state.last_backup_hash == "abc123"
    
    def test_backup_state_to_dict(self):
        timestamp = datetime(2026, 3, 28, 2, 0, 0)
        state = BackupState(user_id=123, last_backup_timestamp=timestamp, last_backup_hash="abc123")
        
        state_dict = state.to_dict()
        
        assert state_dict["user_id"] == 123
        assert state_dict["last_backup_timestamp"] == "2026-03-28T02:00:00"
        assert state_dict["last_backup_hash"] == "abc123"
    
    def test_backup_state_from_dict(self):
        state_dict = {
            "user_id": 456,
            "last_backup_timestamp": "2026-03-28T03:00:00",
            "last_backup_hash": "def456"
        }
        
        state = BackupState.from_dict(state_dict)
        
        assert state.user_id == 456
        assert state.last_backup_timestamp == datetime(2026, 3, 28, 3, 0, 0)
        assert state.last_backup_hash == "def456"
    
    def test_backup_state_with_none_values(self):
        state = BackupState(user_id=789)
        
        assert state.user_id == 789
        assert state.last_backup_timestamp is None
        assert state.last_backup_hash is None
    
    def test_invalid_timestamp_handling(self):
        state_dict = {
            "user_id": 999,
            "last_backup_timestamp": "invalid-date",
            "last_backup_hash": "xyz"
        }
        
        state = BackupState.from_dict(state_dict)
        
        assert state.user_id == 999
        assert state.last_backup_timestamp is None


class TestBackupStateManager:
    def test_save_and_get_state(self, state_manager):
        timestamp = datetime(2026, 3, 28, 2, 0, 0)
        state_manager.save_state(123, timestamp, "abc123")
        
        result = state_manager.get_last_state(123)
        
        assert result is not None
        assert result.user_id == 123
        assert result.last_backup_timestamp == timestamp
        assert result.last_backup_hash == "abc123"
    
    def test_get_nonexistent_state(self, state_manager):
        result = state_manager.get_last_state(999)
        
        assert result is None
    
    def test_multiple_users(self, state_manager):
        state_manager.save_state(111, datetime(2026, 3, 28, 1, 0, 0), "hash1")
        state_manager.save_state(222, datetime(2026, 3, 28, 2, 0, 0), "hash2")
        state_manager.save_state(333, datetime(2026, 3, 28, 3, 0, 0), "hash3")
        
        assert state_manager.get_last_state(111).last_backup_hash == "hash1"
        assert state_manager.get_last_state(222).last_backup_hash == "hash2"
        assert state_manager.get_last_state(333).last_backup_hash == "hash3"
    
    def test_update_state(self, state_manager):
        state_manager.save_state(123, datetime(2026, 3, 28, 1, 0, 0), "hash1")
        state_manager.save_state(123, datetime(2026, 3, 28, 2, 0, 0), "hash2")
        
        result = state_manager.get_last_state(123)
        
        assert result.last_backup_timestamp == datetime(2026, 3, 28, 2, 0, 0)
        assert result.last_backup_hash == "hash2"
    
    def test_get_all_user_ids(self, state_manager):
        state_manager.save_state(111, datetime(2026, 3, 28, 1, 0, 0), "hash1")
        state_manager.save_state(222, datetime(2026, 3, 28, 2, 0, 0), "hash2")
        
        user_ids = state_manager.get_all_user_ids()
        
        assert set(user_ids) == {111, 222}
    
    def test_delete_state(self, state_manager):
        state_manager.save_state(123, datetime(2026, 3, 28, 1, 0, 0), "hash1")
        state_manager.delete_state(123)
        
        result = state_manager.get_last_state(123)
        
        assert result is None
        assert 123 not in state_manager.get_all_user_ids()
    
    def test_state_file_created_automatically(self, temp_dir):
        state_file = Path(temp_dir) / "backup_state.json"
        manager = BackupStateManager(str(state_file))
        
        # File should be created even without calling save_state
        assert state_file.exists()
    
    def test_state_file_persists(self, state_manager):
        state_manager.save_state(123, datetime(2026, 3, 28, 1, 0, 0), "hash1")
        
        # Create new manager instance pointing to same file
        state_file = state_manager.state_file
        new_manager = BackupStateManager(str(state_file))
        
        result = new_manager.get_last_state(123)
        
        assert result is not None
        assert result.last_backup_hash == "hash1"
