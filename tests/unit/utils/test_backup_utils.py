import sys
import pytest

@pytest.fixture(autouse=True)
def cleanup_user_settings():
    """Clean up user settings before each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    if Path(SETTINGS_FILE).exists():
        Path(SETTINGS_FILE).unlink()
    yield

sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import io
import tempfile
import zipfile
from pathlib import Path
from utils.backup_utils import (
    format_file_size,
    create_zip_from_directory,
    extract_zip_to_directory,
    resolve_safe_path,
    list_zip_contents,
    generate_restore_summary
)


class TestFormatFileSize:
    """Tests for format_file_size function."""

    def test_zero_bytes(self):
        """Test formatting of 0 bytes."""
        assert format_file_size(0) == "0.0 B"

    def test_small_bytes(self):
        """Test formatting of small byte values."""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1023) == "1023.0 B"

    def test_one_kb(self):
        """Test formatting of 1 KB."""
        assert format_file_size(1024) == "1.0 KB"

    def test_one_mb(self):
        """Test formatting of 1 MB."""
        assert format_file_size(1048576) == "1.0 MB"

    def test_one_gb(self):
        """Test formatting of 1 GB."""
        assert format_file_size(1073741824) == "1.0 GB"

    def test_half_kb(self):
        """Test formatting of 0.5 KB."""
        result = format_file_size(512)
        assert result == "512.0 B"

    def test_1_5_kb(self):
        """Test formatting of 1.5 KB."""
        result = format_file_size(1536)
        assert result == "1.5 KB"

    def test_large_file(self):
        """Test formatting of large file size."""
        result = format_file_size(2500000000)
        assert "GB" in result

    def test_tb_formatting(self):
        """Test formatting of TB range."""
        result = format_file_size(1099511627776)  # 1 TB
        assert "1.0 TB" in result


class TestCreateZipFromDirectory:
    """Tests for create_zip_from_directory function."""

    def test_empty_directory(self):
        """Test creating ZIP from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            output = io.BytesIO()
            
            count = create_zip_from_directory(source_dir, output)
            
            assert count == 0
            output.seek(0)
            with zipfile.ZipFile(output, 'r') as zf:
                assert len(zf.namelist()) == 0

    def test_single_file(self):
        """Test creating ZIP with single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            test_file = source_dir / "test.txt"
            test_file.write_text("test content")
            
            output = io.BytesIO()
            count = create_zip_from_directory(source_dir, output)
            
            assert count == 1
            output.seek(0)
            with zipfile.ZipFile(output, 'r') as zf:
                assert "test.txt" in zf.namelist()

    def test_multiple_files(self):
        """Test creating ZIP with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            
            # Create test files
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")
            (source_dir / "file3.txt").write_text("content3")
            
            output = io.BytesIO()
            count = create_zip_from_directory(source_dir, output)
            
            assert count == 3

    def test_subdirectories(self):
        """Test creating ZIP with subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            
            # Create subdirectory structure
            subdir = source_dir / "subdir"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("nested content")
            (source_dir / "root.txt").write_text("root content")
            
            output = io.BytesIO()
            count = create_zip_from_directory(source_dir, output)
            
            assert count == 2
            output.seek(0)
            with zipfile.ZipFile(output, 'r') as zf:
                names = zf.namelist()
                assert any("root.txt" in n for n in names)
                assert any("nested.txt" in n for n in names)

    def test_nonexistent_directory(self):
        """Test creating ZIP from non-existent directory."""
        output = io.BytesIO()
        
        with pytest.raises(FileNotFoundError):
            create_zip_from_directory(Path("/nonexistent/path"), output)

    def test_file_instead_of_directory(self):
        """Test creating ZIP from file instead of directory."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test")
            tmpfile_path = Path(tmpfile.name)
        
        output = io.BytesIO()
        
        with pytest.raises(NotADirectoryError):
            create_zip_from_directory(tmpfile_path, output)
        
        tmpfile_path.unlink()


class TestExtractZipToDirectory:
    """Tests for extract_zip_to_directory function."""

    def test_extract_single_file(self):
        """Test extracting single file from ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ZIP with single file
            zip_path = tmpdir / "test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "content1")
            
            extract_dir = tmpdir / "extracted"
            count = extract_zip_to_directory(zip_path, extract_dir)
            
            assert count == 1
            assert (extract_dir / "file1.txt").exists()
            assert (extract_dir / "file1.txt").read_text() == "content1"

    def test_extract_multiple_files(self):
        """Test extracting multiple files from ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ZIP with multiple files
            zip_path = tmpdir / "test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("file2.txt", "content2")
                zf.writestr("file3.txt", "content3")
            
            extract_dir = tmpdir / "extracted"
            count = extract_zip_to_directory(zip_path, extract_dir)
            
            assert count == 3
            assert (extract_dir / "file1.txt").exists()
            assert (extract_dir / "file2.txt").exists()
            assert (extract_dir / "file3.txt").exists()

    def test_extract_subdirectories(self):
        """Test extracting ZIP with subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ZIP with nested structure
            zip_path = tmpdir / "test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("subdir/nested.txt", "nested content")
                zf.writestr("root.txt", "root content")
            
            extract_dir = tmpdir / "extracted"
            count = extract_zip_to_directory(zip_path, extract_dir)
            
            assert count == 2
            assert (extract_dir / "subdir" / "nested.txt").exists()
            assert (extract_dir / "root.txt").exists()

    def test_nonexistent_zip(self):
        """Test extracting non-existent ZIP file."""
        with pytest.raises(FileNotFoundError):
            extract_zip_to_directory(Path("/nonexistent.zip"), Path("/tmp"))

    def test_invalid_zip_file(self):
        """Test extracting invalid ZIP file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmpfile:
            tmpfile.write(b"not a zip file")
            tmpfile_path = Path(tmpfile.name)
        
        with pytest.raises(zipfile.BadZipFile):
            extract_zip_to_directory(tmpfile_path, Path("/tmp"))
        
        tmpfile_path.unlink()


class TestResolveSafePath:
    """Tests for resolve_safe_path function."""

    def test_simple_relative_path(self):
        """Test resolving simple relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            result = resolve_safe_path(base, "subdir/file.txt")
            
            assert result.is_absolute()
            assert str(result).startswith(str(base))

    def test_path_with_dots(self):
        """Test resolving path with . and .. components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            result = resolve_safe_path(base, "./subdir/../file.txt")
            
            assert result.is_absolute()
            assert str(result).startswith(str(base))

    def test_absolute_path_within_base(self):
        """Test resolving absolute path that is within base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subdir = base / "subdir"
            subdir.mkdir()
            
            result = resolve_safe_path(base, str(subdir / "file.txt"))
            
            assert result == subdir / "file.txt"

    def test_path_traversal_attempt(self):
        """Test that path traversal attempts are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            with pytest.raises(ValueError) as exc_info:
                resolve_safe_path(base, "../etc/passwd")
            
            assert "outside base directory" in str(exc_info.value)

    def test_deep_path_traversal(self):
        """Test that deep path traversal attempts are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            with pytest.raises(ValueError):
                resolve_safe_path(base, "subdir/../../../etc/passwd")

    def test_symlink_escape(self):
        """Test that symlink escapes are prevented."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subdir = base / "subdir"
            subdir.mkdir()
            
            # Create a symlink pointing outside base
            outside = Path(tmpdir) / "outside"
            outside.mkdir()
            symlink = subdir / "link"
            symlink.symlink_to(base.parent / "etc")
            
            # This should fail because resolved path is outside base
            with pytest.raises(ValueError):
                resolve_safe_path(base, "subdir/link/passwd")


class TestListZipContents:
    """Tests for list_zip_contents function."""

    def test_empty_zip(self):
        """Test listing contents of empty ZIP."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmpfile:
            zip_path = Path(tmpfile.name)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass
        
        contents = list_zip_contents(zip_path)
        
        assert contents == []
        zip_path.unlink()

    def test_single_file(self):
        """Test listing contents of ZIP with single file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmpfile:
            zip_path = Path(tmpfile.name)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
        
        contents = list_zip_contents(zip_path)
        
        assert "file1.txt" in contents
        zip_path.unlink()

    def test_multiple_files(self):
        """Test listing contents of ZIP with multiple files."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmpfile:
            zip_path = Path(tmpfile.name)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")
            zf.writestr("subdir/file3.txt", "content3")
        
        contents = list_zip_contents(zip_path)
        
        assert "file1.txt" in contents
        assert "file2.txt" in contents
        assert "subdir/file3.txt" in contents
        zip_path.unlink()

    def test_nonexistent_zip(self):
        """Test listing contents of non-existent ZIP."""
        with pytest.raises(FileNotFoundError):
            list_zip_contents(Path("/nonexistent.zip"))

    def test_invalid_zip_file(self):
        """Test listing contents of invalid ZIP file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmpfile:
            tmpfile.write(b"not a zip file")
            tmpfile_path = Path(tmpfile.name)
        
        with pytest.raises(zipfile.BadZipFile):
            list_zip_contents(tmpfile_path)
        
        tmpfile_path.unlink()


def test_generate_restore_summary():
    """Test summary generation with valid validation result."""
    validation_result = {
        'valid': True,
        'stats': {
            'inbox_count': 10,
            'tasks_count': 5,
            'notes_count': 8,
            'archive_count': 3,
            'inbox_backup_count': 2,
        }
    }
    
    summary = generate_restore_summary(validation_result)
    
    assert "Задач:" in summary
    assert "Заметки:" in summary
    assert "ВНИМАНИЕ" in summary
    assert "📦" in summary
    assert "✅ Да, восстановить" in summary
