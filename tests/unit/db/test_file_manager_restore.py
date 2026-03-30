import pytest
from datetime import datetime
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import Task


@pytest.fixture(autouse=True)
def cleanup_user_settings_and_files(tmp_path):
    """Clean up user settings and tmp_path before each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    # Clean up user settings before each test
    if Path(SETTINGS_FILE).exists():
        Path(SETTINGS_FILE).unlink()
    yield
    # Clean up tmp_path after each test to prevent file system state leakage


@pytest.fixture
def unique_user_id():
    """Create unique user_id for each test to prevent cross-test interference"""
    import random
    return 5000000000 + random.randint(0, 1000000)


@pytest.fixture
def fm(unique_user_id, tmp_path):
    """Create FileManager with unique user_id and clean tmp_path"""
    return FileManager(str(tmp_path)), unique_user_id


def test_find_task_in_tasks_success(fm):
    """Найти существующую задачу в активных задачах"""
    fm, user_id = fm
    
    task = Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="completed",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )
    fm.append_task(user_id, task)
    
    result = fm.find_task_in_tasks(user_id, "task_001")
    
    assert result is not None
    assert result.id == "task_001"
    assert result.status == "completed"
    assert result.title == "Тестовая задача"


def test_find_task_in_tasks_not_found(fm):
    """Задача не найдена в активных задачах"""
    fm, user_id = fm
    
    task = Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )
    fm.append_task(user_id, task)
    
    result = fm.find_task_in_tasks(user_id, "task_999")
    
    assert result is None


def test_find_task_in_archive_success(fm, tmp_path):
    """Найти задачу в архиве"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    result = fm.find_task_in_archive(user_id, "task_001")
    
    assert result is not None
    archive_date, task = result
    assert archive_date == "2026-03-28"
    assert task.id == "task_001"
    assert task.status == "completed"


def test_find_task_in_archive_not_found(fm, tmp_path):
    """Задача не найдена в архиве"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    result = fm.find_task_in_archive(user_id, "task_999")
    
    assert result is None


def test_remove_task_from_archive_success(fm, tmp_path):
    """Удалить задачу из архива (файл не пустой)"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Задача 1
tags: []
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тест 1

## task_002
title: Задача 2
tags: []
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тест 2
""")
    
    result = fm.remove_task_from_archive(user_id, "2026-03-28", "task_001")
    
    assert result is True
    assert archive_file.exists()
    
    content = archive_file.read_text()
    assert "task_001" not in content
    assert "task_002" in content


def test_remove_task_from_archive_last_task(fm, tmp_path):
    """Удалить последнюю задачу из архива (удалить файл)"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Задача 1
tags: []
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тест 1
""")
    
    result = fm.remove_task_from_archive(user_id, "2026-03-28", "task_001")
    
    assert result is True
    assert not archive_file.exists()


def test_remove_task_from_archive_not_found(fm, tmp_path):
    """Удалить несуществующую задачу из архива"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Задача 1
tags: []
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тест 1
""")
    
    result = fm.remove_task_from_archive(user_id, "2026-03-28", "task_999")
    
    assert result is False
    assert archive_file.exists()


def test_restore_task_from_archive_success(fm, tmp_path):
    """Переместить задачу из архива в активные"""
    fm, user_id = fm
    
    # Создаем архив с задачей
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    result = fm.restore_task_from_archive(user_id, "task_001")
    
    assert result is True
    assert not archive_file.exists()
    
    tasks = fm.read_tasks(user_id)
    assert len(tasks) == 1
    assert tasks[0].id == "task_001"
    assert tasks[0].status == "pending"
    assert tasks[0].archived_at is None
    assert tasks[0].title == "Архивная задача"


def test_restore_task_from_archive_not_found(fm, tmp_path):
    """Переместить несуществующую задачу из архива"""
    fm, user_id = fm
    
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    result = fm.restore_task_from_archive(user_id, "task_999")
    
    assert result is False
    
    tasks = fm.read_tasks(user_id)
    assert len(tasks) == 0
    assert archive_file.exists()


def test_restore_task_from_archive_task_exists_in_active(fm, tmp_path):
    """Задача существует и в архиве, и в активных (дубликат) - archive обновляет active"""
    fm, user_id = fm
    
    # Создаем задачу в активных
    task = Task(
        id="task_001",
        title="Активная задача",
        tags=["актив"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Активная"
    )
    fm.append_task(user_id, task)
    
    # Создаем дубликат в архиве
    archive_dir = Path(str(tmp_path)) / str(user_id) / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_file = archive_dir / "2026-03-28.md"
    archive_file.write_text("""---
type: archived_tasks
date: 2026-03-28
---

## task_001
title: Архивная задача
tags: [тест]
status: completed
created_at: 2026-03-28T10:00:00
completed_at: 2026-03-28T12:00:00
archived_at: 2026-03-28
source_message_ids: []
content: Тестовая задача
""")
    
    result = fm.restore_task_from_archive(user_id, "task_001")
    
    assert result is True
    assert not archive_file.exists()
    
    tasks = fm.read_tasks(user_id)
    assert len(tasks) == 1
    # Archive данные обновляют активную задачу
    assert tasks[0].title == "Архивная задача"
    assert tasks[0].status == "pending"
    assert tasks[0].archived_at is None
