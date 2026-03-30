import pytest
from datetime import datetime
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import Task


@pytest.fixture(autouse=True)
def cleanup_user_settings(tmp_path):
    """Clean up user settings before each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    settings_path = tmp_path / SETTINGS_FILE
    if settings_path.exists():
        settings_path.unlink()
    yield
    if settings_path.exists():
        settings_path.unlink()


@pytest.fixture
def unique_user_id():
    """Create unique user_id for each test to prevent cross-test interference"""
    import random
    return 5000000000 + random.randint(0, 1000000)


@pytest.fixture
def sample_user_id(unique_user_id):
    """Sample user ID for tests (alias for unique_user_id)"""
    return unique_user_id


@pytest.fixture
def sample_task():
    return Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )


def test_delete_task_success(tmp_path, sample_user_id, sample_task):
    """Тест успешного удаления задачи"""
    fm = FileManager(str(tmp_path))
    
    fm.append_task(sample_user_id, sample_task)
    
    result = fm.delete_task(sample_user_id, "task_001")
    
    assert result is True
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 0


def test_delete_task_not_found(tmp_path, sample_user_id):
    """Тест удаления несуществующей задачи"""
    fm = FileManager(str(tmp_path))
    
    result = fm.delete_task(sample_user_id, "task_999")
    
    assert result is False


def test_delete_task_preserves_others(tmp_path, sample_user_id):
    """Тест что удаление одной задачи не затрагивает другие"""
    fm = FileManager(str(tmp_path))
    
    task1 = Task(
        id="task_001",
        title="Задача 1",
        tags=[],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="1"
    )
    task2 = Task(
        id="task_002",
        title="Задача 2",
        tags=[],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="2"
    )
    fm.append_task(sample_user_id, task1)
    fm.append_task(sample_user_id, task2)
    
    fm.delete_task(sample_user_id, "task_001")
    
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 1
    assert tasks[0].id == "task_002"


def test_delete_task_removes_file_when_empty(tmp_path, sample_user_id, sample_task):
    """Тест что файл удаляется когда задач больше нет"""
    fm = FileManager(str(tmp_path))
    
    fm.append_task(sample_user_id, sample_task)
    
    tasks_dir = tmp_path / str(sample_user_id)
    tasks_file = tasks_dir / "tasks.md"
    
    assert tasks_file.exists()
    
    fm.delete_task(sample_user_id, "task_001")
    
    assert not tasks_file.exists()