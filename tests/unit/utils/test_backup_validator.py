import sys
import pytest
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import io
import tempfile
import zipfile
from pathlib import Path
from utils.backup_validator import BackupValidator


class TestBackupValidator:
    """Tests for BackupValidator class."""

    def test_validate_valid_backup(self):
        """Test validating a valid backup with all required files."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Valid inbox.md
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            # Valid tasks.md
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test, example]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            # Valid notes.md
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test, example]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == True
            assert len(result['errors']) == 0
            assert 'tasks_count' in result['stats']
            assert result['stats']['tasks_count'] == 1
            assert result['stats']['notes_count'] == 1
            assert result['stats']['inbox_count'] == 1
            assert result['stats']['total_files'] == 3
        finally:
            temp_zip.unlink()

    def test_validate_missing_required_files(self):
        """Test validating backup with missing required files."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Only inbox.md, missing tasks.md and notes.md
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert 'errors' in result
            assert 'missing_files' in result
            assert 'tasks.md' in result['missing_files']
            assert 'notes.md' in result['missing_files']
        finally:
            temp_zip.unlink()

    def test_validate_invalid_zip_file(self):
        """Test validating invalid ZIP file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
            f.write(b"This is not a ZIP file")
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('Invalid ZIP' in error for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_nonexistent_file(self):
        """Test validating non-existent file."""
        result = BackupValidator.validate('/nonexistent/path/to/backup.zip')
        
        assert result['valid'] == False
        assert any('not found' in error.lower() for error in result['errors'])

    def test_validate_empty_zip(self):
        """Test validating empty ZIP file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            pass  # Create empty ZIP
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('empty' in error.lower() for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_invalid_yaml_frontmatter(self):
        """Test validating file with invalid YAML frontmatter."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Invalid YAML - unclosed bracket
            zf.writestr('inbox.md', '''---
type: inbox
tags: [invalid
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('YAML' in error for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_duplicate_item_ids(self):
        """Test validating file with duplicate item IDs."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Duplicate IDs
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: First message
chat_id: 456

## msg_001
timestamp: 2026-03-27T10:01:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Duplicate message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('duplicate' in error.lower() for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_missing_required_fields(self):
        """Test validating items with missing required fields."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Missing required fields
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
content: Missing sender_name and chat_id
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('missing required field' in error.lower() for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_invalid_timestamp_format(self):
        """Test validating items with invalid timestamp format."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Invalid timestamp
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: invalid-timestamp
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == False
            assert any('invalid timestamp' in error.lower() for error in result['errors'])
        finally:
            temp_zip.unlink()

    def test_validate_with_archive_files(self):
        """Test validating backup with archive and inbox_backup files."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('archive/2026-03-26.md', 'Archive content')
            zf.writestr('archive/2026-03-25.md', 'More archive content')
            zf.writestr('inbox_backup/inbox_backup_20260326.md', 'Backup content')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == True
            assert result['stats']['archive_count'] == 2
            assert result['stats']['inbox_backup_count'] == 1
            assert result['stats']['total_files'] == 6
        finally:
            temp_zip.unlink()

    def test_validate_multiple_items(self):
        """Test validating backup with multiple items in each file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # Multiple messages
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: User 1
content: Message 1
chat_id: 456

## msg_002
timestamp: 2026-03-27T10:01:00
from_user: 123
sender_id: 123
sender_name: User 1
content: Message 2
chat_id: 456

## msg_003
timestamp: 2026-03-27T10:02:00
from_user: 123
sender_id: 123
sender_name: User 1
content: Message 3
chat_id: 456
''')
            # Multiple tasks
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Task 1
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Content 1

## task_002
title: Task 2
tags: [test]
status: completed
created_at: 2026-03-27T10:01:00
source_message_ids: [msg_002]
content: Content 2
''')
            # Multiple notes
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Note 1
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Content 1

## note_002
title: Note 2
tags: [test]
created_at: 2026-03-27T10:01:00
source_message_ids: [msg_002]
content: Content 2

## note_003
title: Note 3
tags: [test]
created_at: 2026-03-27T10:02:00
source_message_ids: [msg_003]
content: Content 3

## note_004
title: Note 4
tags: [test]
created_at: 2026-03-27T10:03:00
source_message_ids: [msg_001]
content: Content 4

## note_005
title: Note 5
tags: [test]
created_at: 2026-03-27T10:04:00
source_message_ids: [msg_002]
content: Content 5
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == True
            assert result['stats']['inbox_count'] == 3
            assert result['stats']['tasks_count'] == 2
            assert result['stats']['notes_count'] == 5
        finally:
            temp_zip.unlink()

    def test_validate_warnings_for_mismatched_types(self):
        """Test that warnings are generated for mismatched file types."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # inbox.md with wrong type
            zf.writestr('inbox.md', '''---
type: note
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            # Should be valid but with warnings
            assert result['valid'] == True
            assert len(result['warnings']) > 0
            assert any('inbox.md' in warning for warning in result['warnings'])
        finally:
            temp_zip.unlink()

    def test_no_file_modifications_during_validation(self):
        """Test that validation does not modify any files."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            zf.writestr('inbox.md', '''---
type: inbox
---

## msg_001
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: Test User
content: Test message
chat_id: 456
''')
            zf.writestr('tasks.md', '''---
type: task
---

## task_001
title: Test task
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
            zf.writestr('notes.md', '''---
type: note
---

## note_001
title: Test note
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Test content
''')
        
        zip_mtime = temp_zip.stat().st_mtime
        
        try:
            BackupValidator.validate(temp_zip)
            
            # File should not be modified
            assert temp_zip.stat().st_mtime == zip_mtime
        finally:
            temp_zip.unlink()

    def test_statistics_accuracy(self):
        """Test that statistics are accurately counted."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            temp_zip = Path(f.name)
        
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            # 5 messages in inbox.md
            inbox_content = '---\ntype: inbox\n---\n\n'
            for i in range(5):
                inbox_content += f'''## msg_{i:03d}
timestamp: 2026-03-27T10:00:00
from_user: 123
sender_id: 123
sender_name: User
content: Message {i}
chat_id: 456

'''
            zf.writestr('inbox.md', inbox_content)
            
            # 3 tasks in tasks.md
            tasks_content = '---\ntype: task\n---\n\n'
            for i in range(3):
                tasks_content += f'''## task_{i:03d}
title: Task {i}
tags: [test]
status: pending
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Content {i}

'''
            zf.writestr('tasks.md', tasks_content)
            
            # 4 notes in notes.md
            notes_content = '---\ntype: note\n---\n\n'
            for i in range(4):
                notes_content += f'''## note_{i:03d}
title: Note {i}
tags: [test]
created_at: 2026-03-27T10:00:00
source_message_ids: [msg_001]
content: Content {i}

'''
            zf.writestr('notes.md', notes_content)
        
        try:
            result = BackupValidator.validate(temp_zip)
            
            assert result['valid'] == True
            assert result['stats']['inbox_count'] == 5
            assert result['stats']['tasks_count'] == 3
            assert result['stats']['notes_count'] == 4
        finally:
            temp_zip.unlink()
