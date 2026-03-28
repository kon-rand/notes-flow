"""
Backup validator module for validating backup ZIP files.

This module provides the BackupValidator class for validating backup archives
created by the FileManager. It checks ZIP structure, YAML frontmatter, data integrity,
and generates statistics about the backup contents.
"""

import zipfile
import io
import tempfile
import shutil
from pathlib import Path
from typing import Any
import yaml  # type: ignore[import-untyped]
from datetime import datetime


class BackupValidator:
    """
    Validator for backup ZIP files.
    
    Validates ZIP structure, YAML frontmatter in each file,
    data integrity (unique IDs, valid dates), and generates statistics.
    
    Attributes:
        errors: List of validation error messages.
        warnings: List of validation warning messages.
        stats: Dictionary containing backup statistics.
    """
    
    REQUIRED_FILES = ['inbox.md', 'tasks.md', 'notes.md']
    
    def __init__(self) -> None:
        """Initialize the validator with empty error/warning lists."""
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict[str, Any] = {
            'total_files': 0,
            'inbox_count': 0,
            'tasks_count': 0,
            'notes_count': 0,
            'archive_count': 0,
            'inbox_backup_count': 0,
        }
    
    @classmethod
    def validate(cls, zip_path: str | Path) -> dict[str, Any]:
        """
        Validate a backup ZIP file.
        
        This is a convenience method that creates a validator instance and
        performs validation without maintaining state.
        
        Args:
            zip_path: Path to the ZIP file to validate.
            
        Returns:
            Dictionary containing validation result with the following keys:
                - valid: bool indicating if validation passed
                - errors: list of error messages
                - warnings: list of warning messages
                - stats: dictionary containing backup statistics
                - missing_files: list of missing required files (if invalid)
                
        Raises:
            FileNotFoundError: If ZIP file does not exist.
            zipfile.BadZipFile: If file is not a valid ZIP archive.
            
        Examples:
            >>> import io
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            ...     temp_zip = Path(f.name)
            >>> with zipfile.ZipFile(temp_zip, 'w') as zf:
            ...     zf.writestr('inbox.md', '---\\ntype: inbox\\n---\\n\\n## msg_001\\ntimestamp: 2026-03-27T10:00:00\\nfrom_user: 123\\nsender_id: 123\\nsender_name: Test\\ncontent: Test message\\nchat_id: 456')
            ...     zf.writestr('tasks.md', '---\\ntype: task\\n---\\n\\n## task_001\\ntitle: Test task\\ntags: [test]\\nstatus: pending\\ncreated_at: 2026-03-27T10:00:00\\nsource_message_ids: [msg_001]\\ncontent: Test content')
            ...     zf.writestr('notes.md', '---\\ntype: note\\n---\\n\\n## note_001\\ntitle: Test note\\ntags: [test]\\ncreated_at: 2026-03-27T10:00:00\\nsource_message_ids: [msg_001]\\ncontent: Test content')
            >>> result = BackupValidator.validate(temp_zip)
            >>> result['valid']
            True
            >>> 'tasks_count' in result['stats']
            True
            >>> temp_zip.unlink()
        """
        validator = cls()
        return validator._validate_zip(Path(zip_path))
    
    def _validate_zip(self, zip_path: Path) -> dict[str, Any]:
        """
        Perform full validation of a ZIP file.
        
        Args:
            zip_path: Path to the ZIP file to validate.
            
        Returns:
            Dictionary containing validation result.
        """
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_files': 0,
            'inbox_count': 0,
            'tasks_count': 0,
            'notes_count': 0,
            'archive_count': 0,
            'inbox_backup_count': 0,
        }
        
        zip_file = Path(zip_path)
        
        if not zip_file.exists():
            self.errors.append(f"ZIP file not found: {zip_path}")
            return self._build_result()
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
        except zipfile.BadZipFile:
            self.errors.append(f"Invalid ZIP file: {zip_path}")
            return self._build_result()
        
        if not file_list:
            self.errors.append("ZIP file is empty")
            return self._build_result()
        
        self.stats['total_files'] = len(file_list)
        
        required_files = []
        for required in self.REQUIRED_FILES:
            if required in file_list:
                required_files.append(required)
            else:
                self.errors.append(f"Missing required file: {required}")
        
        if self.errors:
            return self._build_result()
        
        temp_dir = None
        
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix='backup_validate_'))
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            for required_file in required_files:
                file_path = temp_dir / required_file
                self._validate_file_structure(required_file, file_path)
            
            for filename in file_list:
                if filename.startswith('archive/'):
                    self.stats['archive_count'] += 1
                elif filename.startswith('inbox_backup/'):
                    self.stats['inbox_backup_count'] += 1
            
            return self._build_result()
            
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return self._build_result()
            
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _validate_file_structure(self, filename: str, file_path: Path) -> None:
        """
        Validate the structure of a single file.
        
        Args:
            filename: Name of the file being validated.
            file_path: Path to the file.
        """
        if not file_path.exists():
            self.errors.append(f"File not found during validation: {filename}")
            return
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Cannot read file {filename}: {str(e)}")
            return
        
        parts = content.split('---\n')
        
        if len(parts) < 3:
            self.errors.append(f"File {filename} has invalid format: missing YAML frontmatter")
            return
        
        try:
            metadata = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            self.errors.append(f"File {filename} has invalid YAML frontmatter: {str(e)}")
            return
        
        if not isinstance(metadata, dict):
            self.errors.append(f"File {filename} has invalid YAML frontmatter: expected dict")
            return
        
        metadata_type = metadata.get('type')
        
        if metadata_type is None:
            self.warnings.append(f"File {filename} has no 'type' in frontmatter")
            return
        
        expected_types = {
            'inbox': 'inbox.md',
            'task': 'tasks.md',
            'note': 'notes.md',
        }
        
        expected_type = expected_types.get(filename.replace('.md', ''))
        
        if expected_type:
            expected_metadata_type = expected_type.replace('.md', '')
            if metadata_type != expected_metadata_type:
                self.warnings.append(
                    f"File {filename} has type='{metadata_type}', expected '{expected_metadata_type}'"
                )
        
        # Extract body content after the frontmatter (parts[2])
        body_content = parts[2].strip()
        item_blocks = body_content.split('\n## ')
        
        items = []
        for block in item_blocks:
            block = block.strip()
            if not block:
                continue
            
            lines = block.split('\n')
            if not lines:
                continue
            
            item_id = lines[0].strip().lstrip('#').strip()
            
            if not item_id:
                self.errors.append(f"File {filename} has empty item ID")
                continue
            
            item_data: dict[str, Any] = {}
            for line in lines[1:]:
                if ':' not in line:
                    continue
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                key = parts[0].strip()
                value = parts[1].strip()
                
                if value == 'null':
                    item_data[key] = None
                elif value.startswith('[') and value.endswith(']'):
                    inner = value[1:-1].strip()
                    if inner:
                        item_data[key] = [x.strip().strip('"').strip("'") for x in inner.split(',')]
                    else:
                        item_data[key] = []
                else:
                    try:
                        item_data[key] = datetime.fromisoformat(value)
                    except ValueError:
                        item_data[key] = value
            
            if item_id in [i[0] for i in items]:
                self.errors.append(f"File {filename} has duplicate item ID: {item_id}")
                continue
            
            items.append((item_id, item_data))
        
        if filename == 'inbox.md':
            self.stats['inbox_count'] = len(items)
            self._validate_inbox_items(items, file_path)
            
        elif filename == 'tasks.md':
            self.stats['tasks_count'] = len(items)
            self._validate_task_items(items, file_path)
            
        elif filename == 'notes.md':
            self.stats['notes_count'] = len(items)
            self._validate_note_items(items, file_path)
    
    def _validate_inbox_items(self, items: list[tuple[str, dict[str, Any]]], file_path: Path) -> None:
        """
        Validate inbox message items.
        
        Args:
            items: List of (id, data) tuples.
            file_path: Path to the file for error messages.
        """
        required_fields = ['timestamp', 'from_user', 'sender_id', 'content', 'chat_id']
        
        for item_id, item_data in items:
            for field in required_fields:
                if field not in item_data:
                    self.errors.append(
                        f"File {file_path.name} item {item_id} missing required field: {field}"
                    )
            
            if 'timestamp' in item_data and item_data['timestamp'] is not None:
                if not isinstance(item_data['timestamp'], datetime):
                    try:
                        datetime.fromisoformat(str(item_data['timestamp']))
                    except (ValueError, TypeError):
                        self.errors.append(
                            f"File {file_path.name} item {item_id} has invalid timestamp format"
                        )
    
    def _validate_task_items(self, items: list[tuple[str, dict[str, Any]]], file_path: Path) -> None:
        """
        Validate task items.
        
        Args:
            items: List of (id, data) tuples.
            file_path: Path to the file for error messages.
        """
        required_fields = ['title', 'tags', 'status', 'created_at', 'source_message_ids', 'content']
        
        for item_id, item_data in items:
            for field in required_fields:
                if field not in item_data:
                    self.errors.append(
                        f"File {file_path.name} item {item_id} missing required field: {field}"
                    )
            
            if 'created_at' in item_data and item_data['created_at'] is not None:
                if not isinstance(item_data['created_at'], datetime):
                    try:
                        datetime.fromisoformat(str(item_data['created_at']))
                    except (ValueError, TypeError):
                        self.errors.append(
                            f"File {file_path.name} item {item_id} has invalid created_at format"
                        )
    
    def _validate_note_items(self, items: list[tuple[str, dict[str, Any]]], file_path: Path) -> None:
        """
        Validate note items.
        
        Args:
            items: List of (id, data) tuples.
            file_path: Path to the file for error messages.
        """
        required_fields = ['title', 'tags', 'created_at', 'source_message_ids', 'content']
        
        for item_id, item_data in items:
            for field in required_fields:
                if field not in item_data:
                    self.errors.append(
                        f"File {file_path.name} item {item_id} missing required field: {field}"
                    )
            
            if 'created_at' in item_data and item_data['created_at'] is not None:
                if not isinstance(item_data['created_at'], datetime):
                    try:
                        datetime.fromisoformat(str(item_data['created_at']))
                    except (ValueError, TypeError):
                        self.errors.append(
                            f"File {file_path.name} item {item_id} has invalid created_at format"
                        )
    
    def _build_result(self) -> dict[str, Any]:
        """
        Build the validation result dictionary.
        
        Returns:
            Dictionary containing validation result.
        """
        missing_files = []
        for required in self.REQUIRED_FILES:
            if f"Missing required file: {required}" in self.errors:
                missing_files.append(required)
        
        result = {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': self.stats,
        }
        
        if not result['valid']:
            result['missing_files'] = missing_files
        
        return result

import logging
logger = logging.getLogger(__name__)

def has_changes(user_id: int, last_backup_timestamp: datetime, data_dir: str = "data") -> bool:
    user_dir = Path(data_dir) / str(user_id)
    if not user_dir.exists():
        logger.warning(f"User data directory not found: {user_dir}")
        return False
    
    files_to_check = _get_files_to_check(user_dir)
    for file_path in files_to_check:
        try:
            if file_path.exists() and file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > last_backup_timestamp:
                    logger.debug(f"File changed: {file_path.name} (modified: {mtime.isoformat()}, last_backup: {last_backup_timestamp.isoformat()})")
                    return True
        except OSError as e:
            logger.warning(f"Failed to stat file {file_path}: {e}")
    return False


def _get_files_to_check(user_dir: Path) -> list[Path]:
    files = []
    for filename in ['inbox.md', 'tasks.md', 'notes.md']:
        files.append(user_dir / filename)
    archive_dir = user_dir / 'archive'
    if archive_dir.exists() and archive_dir.is_dir():
        for file_path in archive_dir.glob('*.md'):
            files.append(file_path)
    inbox_backup_dir = user_dir / 'inbox_backup'
    if inbox_backup_dir.exists() and inbox_backup_dir.is_dir():
        for file_path in inbox_backup_dir.glob('*.md'):
            files.append(file_path)
    return files
