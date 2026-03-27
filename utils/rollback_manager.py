"""
Rollback manager for backup/restore functionality.
"""

import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional


class RollbackError(Exception):
    """Exception raised when rollback operation fails."""
    pass


class RollbackManager:
    """
    Manages rollback operations for backup/restore functionality.
    """
    
    def __init__(self, user_id: int, data_dir: str = "data") -> None:
        self.user_id = user_id
        self.data_dir = Path(data_dir)
        self.backup_path: Optional[Path] = None
        self._backup_created = False
    
    def _get_user_dir(self) -> Path:
        return self.data_dir / str(self.user_id)
    
    def _get_backup_path(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"rollback_{self.user_id}_{timestamp}"
        temp_dir = Path(tempfile.gettempdir())
        return temp_dir / backup_name
    
    def create_backup(self) -> bool:
        try:
            user_dir = self._get_user_dir()
            
            if not user_dir.exists():
                self.backup_path = user_dir
                self._backup_created = True
                return True
            
            self.backup_path = self._get_backup_path()
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            files_to_backup = ['inbox.md', 'tasks.md', 'notes.md']
            
            for filename in files_to_backup:
                src = user_dir / filename
                if src.exists():
                    dst = self.backup_path / filename
                    shutil.copy2(src, dst)
            
            archive_dir = user_dir / 'archive'
            if archive_dir.exists():
                target_archive = self.backup_path / 'archive'
                target_archive.mkdir(parents=True, exist_ok=True)
                for file_path in archive_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_archive / file_path.name)
            
            inbox_backup_dir = user_dir / 'inbox_backup'
            if inbox_backup_dir.exists():
                target_inbox_backup = self.backup_path / 'inbox_backup'
                target_inbox_backup.mkdir(parents=True, exist_ok=True)
                for file_path in inbox_backup_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_inbox_backup / file_path.name)
            
            self._backup_created = True
            return True
            
        except Exception as e:
            raise RollbackError(f"Failed to create backup: {str(e)}")
    
    def rollback(self) -> bool:
        if not self._backup_created or self.backup_path is None:
            raise RollbackError("No backup exists to rollback to")
        
        try:
            user_dir = self._get_user_dir()
            user_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_restore = ['inbox.md', 'tasks.md', 'notes.md']
            
            for filename in files_to_restore:
                src = self.backup_path / filename
                if src.exists():
                    dst = user_dir / filename
                    shutil.copy2(src, dst)
            
            archive_dir = self.backup_path / 'archive'
            if archive_dir.exists():
                target_archive = user_dir / 'archive'
                target_archive.mkdir(parents=True, exist_ok=True)
                for file_path in archive_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_archive / file_path.name)
            
            inbox_backup_dir = self.backup_path / 'inbox_backup'
            if inbox_backup_dir.exists():
                target_inbox_backup = user_dir / 'inbox_backup'
                target_inbox_backup.mkdir(parents=True, exist_ok=True)
                for file_path in inbox_backup_dir.glob('*'):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_inbox_backup / file_path.name)
            
            return True
            
        except Exception as e:
            raise RollbackError(f"Failed to rollback: {str(e)}")
    
    def cleanup(self) -> bool:
        if self.backup_path is None or not self.backup_path.exists():
            return True
        
        try:
            shutil.rmtree(self.backup_path)
            self._backup_created = False
            return True
            
        except Exception as e:
            raise RollbackError(f"Failed to cleanup backup: {str(e)}")
    
    def __enter__(self) -> 'RollbackManager':
        if not self._backup_created:
            self.create_backup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                self.rollback()
            except RollbackError:
                pass
        else:
            try:
                self.cleanup()
            except RollbackError:
                pass
