"""
Utility functions for backup and file operations.

This module provides helper functions for file size formatting,
ZIP archive creation/extraction, and safe path resolution.
"""

import hashlib
import io
import zipfile
from pathlib import Path
from typing import Any, List


def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes to convert.

    Returns:
        Human-readable string representation of the size.

    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
        >>> format_file_size(1073741824)
        '1.0 GB'
        >>> format_file_size(500)
        '500.0 B'
    """
    if size_bytes < 1024:
        return f"{float(size_bytes):.1f} B"
    
    units = ['KB', 'MB', 'GB', 'TB', 'PB']
    size = float(size_bytes)
    
    for unit in units:
        size /= 1024
        if size < 1024:
            return f"{size:.1f} {unit}"
    
    return f"{size:.1f} PB"


def create_zip_from_directory(source_dir: Path, zip_output: io.BytesIO) -> int:
    """
    Create ZIP archive from directory contents.

    Args:
        source_dir: Path to the directory to archive.
        zip_output: BytesIO object to write the ZIP archive to.

    Returns:
        Number of files added to the archive.

    Raises:
        FileNotFoundError: If source directory does not exist.
        NotADirectoryError: If source path is not a directory.

    Examples:
        >>> import io
        >>> from pathlib import Path
        >>> temp_dir = Path("/tmp/test_dir")
        >>> temp_dir.mkdir(exist_ok=True)
        >>> (temp_dir / "file1.txt").write_text("content1")
        >>> (temp_dir / "file2.txt").write_text("content2")
        >>> output = io.BytesIO()
        >>> count = create_zip_from_directory(temp_dir, output)
        >>> count
        2
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Directory not found: {source_dir}")
    
    if not source_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {source_dir}")
    
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        files_added = 0
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                arc_name = file_path.relative_to(source_path)
                zip_file.write(file_path, arc_name)
                files_added += 1
        
        return files_added


def extract_zip_to_directory(zip_path: Path, target_dir: Path) -> int:
    """
    Extract ZIP file to target directory.

    Args:
        zip_path: Path to the ZIP file to extract.
        target_dir: Directory to extract files to.

    Returns:
        Number of files extracted.

    Raises:
        FileNotFoundError: If ZIP file does not exist.
        zipfile.BadZipFile: If file is not a valid ZIP archive.
    """
    zip_file = Path(zip_path)
    
    if not zip_file.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(target_path)
        
        return len(zip_ref.namelist())


def resolve_safe_path(base_dir: Path, relative_path: str) -> Path:
    """
    Resolve a safe path within base directory (prevents path traversal).

    Args:
        base_dir: Base directory that serves as the root for safe paths.
        relative_path: Relative path to resolve within base directory.

    Returns:
        Resolved absolute path within base directory.

    Raises:
        ValueError: If resolved path is outside base directory (path traversal attempt).

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     base = Path(tmpdir)
        ...     safe = resolve_safe_path(base, "subdir/file.txt")
        ...     str(safe).startswith(str(base))
        True
        >>> resolve_safe_path(Path("/tmp"), "../etc/passwd")
        Traceback (most recent call last):
            ...
        ValueError: Resolved path is outside base directory
    """
    base = Path(base_dir).resolve()
    relative = Path(relative_path)
    
    # Handle both absolute and relative paths
    if relative.is_absolute():
        resolved = relative
    else:
        resolved = base / relative
    
    resolved = resolved.resolve()
    
    # Ensure the resolved path is within the base directory
    try:
        resolved.relative_to(base)
    except ValueError:
        raise ValueError("Resolved path is outside base directory")
    
    return resolved


def list_zip_contents(zip_path: Path) -> List[str]:
    """
    List all files in a ZIP archive.

    Args:
        zip_path: Path to the ZIP file.

    Returns:
        List of file paths within the ZIP archive.

    Raises:
        FileNotFoundError: If ZIP file does not exist.
        zipfile.BadZipFile: If file is not a valid ZIP archive.

    Examples:
        >>> import io
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        ...     temp_zip = Path(f.name)
        >>> with zipfile.ZipFile(temp_zip, 'w') as zf:
        ...     zf.writestr('file1.txt', 'content1')
        ...     zf.writestr('file2.txt', 'content2')
        >>> contents = list_zip_contents(temp_zip)
        >>> 'file1.txt' in contents
        True
        >>> 'file2.txt' in contents
        True
    """
    zip_file = Path(zip_path)
    
    if not zip_file.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        return zip_ref.namelist()


def generate_restore_summary(validation_result: dict[str, Any]) -> str:
    """
    Generate a formatted summary text for restore confirmation.
    
    Args:
        validation_result: Result from BackupValidator.validate()
        
    Returns:
        Formatted summary string for Telegram display
    """
    stats = validation_result.get('stats', {})
    
    summary_lines = [
        "📦 Предварительный просмотр бэкапа:",
        "",
        "📊 Статистика:",
        f"• Задач: {stats.get('tasks_count', 0)}",
        f"• Заметки: {stats.get('notes_count', 0)}",
        f"• Сообщений в инбоксе: {stats.get('inbox_count', 0)}",
        f"• Задач в архиве: {stats.get('archive_count', 0)}",
        f"• Старых бэкапов inbox: {stats.get('inbox_backup_count', 0)}",
        "",
        "⚠️ ВНИМАНИЕ!",
        "Восстановление заменит ВСЕ текущие данные на данные из бэкапа.",
        "Существующие данные будут удалены безвозвратно.",
        "",
        "Вы уверены, что хотите продолжить?",
        "✅ Да, восстановить",
        "❌ Отмена",
    ]
    
    return "\n".join(summary_lines)
