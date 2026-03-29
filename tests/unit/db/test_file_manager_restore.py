import pytest
from datetime import datetime
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import Task


@pytest.fixture
def sample_user_id():
    return 123456789


@pytest.fixture
def sample_completed_task():
    return Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="completed",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )


def test_find_task_in_tasks_success(tmp_path, sample_user_id):
    """Найти существующую задачу в активных задачах"""
    fm = FileManager(str(tmp_path))
    
    task = Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="completed",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )
    fm.append_task(sample_user_id, task)
    
    result = fm.find_task_in_tasks(sample_user_id, "task_001")
    
    assert result is not None
    assert result.id == "task_001"
    assert result.status == "completed"
    assert result.title == "Тестовая задача"


def test_find_task_in_tasks_not_found(tmp_path, sample_user_id):
    """Задача не найдена в активных задачах"""
    fm = FileManager(str(tmp_path))
    
    task = Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )
    fm.append_task(sample_user_id, task)
    
    result = fm.find_task_in_tasks(sample_user_id, "task_999")
    
    assert result is None


def test_find_task_in_archive_success(tmp_path, sample_user_id):
    """Найти задачу в архиве"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.find_task_in_archive(sample_user_id, "task_001")
    
    assert result is not None
    archive_date, task = result
    assert archive_date == "2026-03-28"
    assert task.id == "task_001"
    assert task.status == "completed"


def test_find_task_in_archive_not_found(tmp_path, sample_user_id):
    """Задача не найдена в архиве"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.find_task_in_archive(sample_user_id, "task_999")
    
    assert result is None


def test_remove_task_from_archive_success(tmp_path, sample_user_id):
    """Удалить задачу из архива (файл не пустой)"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.remove_task_from_archive(sample_user_id, "2026-03-28", "task_001")
    
    assert result is True
    assert archive_file.exists()
    
    content = archive_file.read_text()
    assert "task_001" not in content
    assert "task_002" in content


def test_remove_task_from_archive_last_task(tmp_path, sample_user_id):
    """Удалить последнюю задачу из архива (удалить файл)"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.remove_task_from_archive(sample_user_id, "2026-03-28", "task_001")
    
    assert result is True
    assert not archive_file.exists()


def test_remove_task_from_archive_not_found(tmp_path, sample_user_id):
    """Удалить несуществующую задачу из архива"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.remove_task_from_archive(sample_user_id, "2026-03-28", "task_999")
    
    assert result is False
    assert archive_file.exists()


def test_restore_task_from_archive_success(tmp_path, sample_user_id):
    """Переместить задачу из архива в активные"""
    fm = FileManager(str(tmp_path))
    
    # Создаем архив с задачей
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.restore_task_from_archive(sample_user_id, "task_001")
    
    assert result is True
    assert not archive_file.exists()
    
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 1
    assert tasks[0].id == "task_001"
    assert tasks[0].status == "pending"
    assert tasks[0].archived_at is None
    assert tasks[0].title == "Архивная задача"


def test_restore_task_from_archive_not_found(tmp_path, sample_user_id):
    """Переместить несуществующую задачу из архива"""
    fm = FileManager(str(tmp_path))
    
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.restore_task_from_archive(sample_user_id, "task_999")
    
    assert result is False
    
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 0
    assert archive_file.exists()


def test_restore_task_from_archive_task_exists_in_active(tmp_path, sample_user_id):
    """Задача существует и в архиве, и в активных (дубликат) - archive обновляет active"""
    fm = FileManager(str(tmp_path))
    
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
    fm.append_task(sample_user_id, task)
    
    # Создаем дубликат в архиве
    archive_dir = Path(str(tmp_path)) / str(sample_user_id) / "archive"
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
    
    result = fm.restore_task_from_archive(sample_user_id, "task_001")
    
    assert result is True
    assert not archive_file.exists()
    
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 1
    # Archive данные обновляют активную задачу
    assert tasks[0].title == "Архивная задача"
    assert tasks[0].status == "pending"
    assert tasks[0].archived_at is None
