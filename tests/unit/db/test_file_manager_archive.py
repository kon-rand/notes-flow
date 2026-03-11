import pytest
from datetime import datetime
from pathlib import Path

from bot.db.file_manager import FileManager
from bot.db.models import Task


@pytest.fixture
def tmp_user_dir(tmp_path):
    """Создать временную директорию для тестов пользователя"""
    user_id = 999999
    user_dir = tmp_path / str(user_id)
    user_dir.mkdir()
    return user_dir, user_id, tmp_path


class TestArchiveCompletedTasks:
    def test_archive_completed_tasks(self, tmp_user_dir):
        """Проверить архивацию выполненных задач"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        completed_at = datetime(2026, 3, 10, 9, 0)
        
        task1 = Task(
            id="task_001",
            title="Тестовая задача 1",
            tags=["тест"],
            status="completed",
            created_at=datetime(2026, 3, 9, 10, 0),
            completed_at=completed_at,
            source_message_ids=[],
            content="Тест 1"
        )
        task2 = Task(
            id="task_002",
            title="Тестовая задача 2",
            tags=["работа"],
            status="completed",
            created_at=datetime(2026, 3, 9, 11, 0),
            completed_at=completed_at,
            source_message_ids=[],
            content="Тест 2"
        )
        pending_task = Task(
            id="task_003",
            title="Висит задача",
            tags=[],
            status="pending",
            created_at=datetime(2026, 3, 9, 12, 0),
            completed_at=None,
            source_message_ids=[],
            content="Не завершена"
        )

        fm.append_task(user_id, task1)
        fm.append_task(user_id, task2)
        fm.append_task(user_id, pending_task)

        archive_date = datetime(2026, 3, 10)
        archived = fm.archive_completed_tasks(user_id, archive_date)

        assert len(archived) == 2
        assert all(t.archived_at is not None for t in archived)
        assert all(t.archived_at.date() == archive_date.date() for t in archived)

        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].id == "task_003"

        archive_tasks = fm.get_tasks_by_archive_date(user_id, "2026-03-10")
        assert len(archive_tasks) == 2
        archive_ids = {t.id for t in archive_tasks}
        assert "task_001" in archive_ids
        assert "task_002" in archive_ids

    def test_archive_completed_tasks_no_completed(self, tmp_user_dir):
        """Архивация когда нет выполненных задач"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        task = Task(
            id="task_001",
            title="Висит задача",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            completed_at=None,
            source_message_ids=[],
            content="Тест"
        )
        fm.append_task(user_id, task)

        archived = fm.archive_completed_tasks(user_id, datetime.now())
        assert len(archived) == 0

        tasks = fm.read_tasks(user_id)
        assert len(tasks) == 1

    def test_archive_completed_tasks_different_dates(self, tmp_user_dir):
        """Архивация задач с разными датами выполнения"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        task1 = Task(
            id="task_001",
            title="Задача 1",
            tags=[],
            status="completed",
            created_at=datetime(2026, 3, 9, 10, 0),
            completed_at=datetime(2026, 3, 10, 9, 0),
            source_message_ids=[],
            content="Тест 1"
        )
        task2 = Task(
            id="task_002",
            title="Задача 2",
            tags=[],
            status="completed",
            created_at=datetime(2026, 3, 9, 11, 0),
            completed_at=datetime(2026, 3, 11, 9, 0),
            source_message_ids=[],
            content="Тест 2"
        )

        fm.append_task(user_id, task1)
        fm.append_task(user_id, task2)

        archived = fm.archive_completed_tasks(user_id, datetime(2026, 3, 10))
        assert len(archived) == 1
        assert archived[0].id == "task_001"

        archived_11 = fm.archive_completed_tasks(user_id, datetime(2026, 3, 11))
        assert len(archived_11) == 1
        assert archived_11[0].id == "task_002"


class TestGetArchiveDates:
    def test_get_archive_dates(self, tmp_user_dir):
        """Получение списка дат архива"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        archive_dir = user_dir / "archive"
        archive_dir.mkdir()

        (archive_dir / "2026-03-10.md").write_text("---\ntype: archived_tasks\ndate: 2026-03-10\n---\n\n## task_001\ntitle: Task 1\n")
        (archive_dir / "2026-03-11.md").write_text("---\ntype: archived_tasks\ndate: 2026-03-11\n---\n\n## task_002\ntitle: Task 2\n")

        dates = fm.get_archive_dates(user_id)

        assert "2026-03-10" in dates
        assert "2026-03-11" in dates
        assert dates == sorted(dates)

    def test_get_archive_dates_empty(self, tmp_user_dir):
        """Получение списка дат когда архив пуст"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        dates = fm.get_archive_dates(user_id)
        assert dates == []

    def test_get_archive_dates_no_archive_dir(self, tmp_user_dir):
        """Получение списка дат когда папка архива не существует"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        dates = fm.get_archive_dates(user_id)
        assert dates == []


class TestGetTasksByArchiveDate:
    def test_get_tasks_by_archive_date(self, tmp_user_dir):
        """Получение задач из архива за указанную дату"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        archive_dir = user_dir / "archive"
        archive_dir.mkdir()

        archive_content = """---
type: archived_tasks
date: 2026-03-10
---

## task_001
title: Тестовая задача
tags: [работа, тест]
status: completed
created_at: 2026-03-09T10:00:00
completed_at: 2026-03-10T09:00:00
archived_at: 2026-03-10T02:00:00
source_message_ids: [msg_001, msg_002]
content: Отчёт подготовлен
"""
        (archive_dir / "2026-03-10.md").write_text(archive_content)

        tasks = fm.get_tasks_by_archive_date(user_id, "2026-03-10")

        assert len(tasks) == 1
        assert tasks[0].id == "task_001"
        assert tasks[0].title == "Тестовая задача"
        assert tasks[0].tags == ["работа", "тест"]
        assert tasks[0].status == "completed"
        assert tasks[0].content == "Отчёт подготовлен"

    def test_get_tasks_by_archive_date_not_found(self, tmp_user_dir):
        """Получение задач когда файл архива не существует"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        tasks = fm.get_tasks_by_archive_date(user_id, "2026-03-10")
        assert tasks == []

    def test_get_tasks_by_archive_date_empty(self, tmp_user_dir):
        """Получение задач когда файл архива пустой"""
        user_dir, user_id, tmp_path = tmp_user_dir
        fm = FileManager(str(tmp_path))

        archive_dir = user_dir / "archive"
        archive_dir.mkdir()
        (archive_dir / "2026-03-10.md").write_text("---\ntype: archived_tasks\n---\n")

        tasks = fm.get_tasks_by_archive_date(user_id, "2026-03-10")
        assert tasks == []