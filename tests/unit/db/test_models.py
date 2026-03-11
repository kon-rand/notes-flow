import pytest
from datetime import datetime
from bot.db.models import Task


class TestTaskModel:
    """Тесты для модели Task с новыми полями"""

    def test_task_default_values(self):
        """Проверить значения по умолчанию для completed_at и archived_at"""
        task = Task(
            id="task_001",
            title="Тестовая задача",
            tags=["test"],
            created_at=datetime(2026, 3, 10, 10, 0),
            source_message_ids=[],
            content=""
        )
        
        assert task.status == "pending"
        assert task.completed_at is None
        assert task.archived_at is None

    def test_task_with_completed_at(self):
        """Проверить установку completed_at"""
        completed_time = datetime(2026, 3, 10, 14, 30)
        task = Task(
            id="task_002",
            title="Выполненная задача",
            tags=["work"],
            status="completed",
            created_at=datetime(2026, 3, 10, 10, 0),
            completed_at=completed_time,
            source_message_ids=[],
            content=""
        )
        
        assert task.status == "completed"
        assert task.completed_at == completed_time
        assert task.archived_at is None

    def test_task_with_archived_at(self):
        """Проверить установку archived_at"""
        archive_time = datetime(2026, 3, 10, 2, 0)
        task = Task(
            id="task_003",
            title="Архивная задача",
            tags=["old"],
            status="completed",
            created_at=datetime(2026, 3, 9, 10, 0),
            completed_at=datetime(2026, 3, 10, 9, 0),
            archived_at=archive_time,
            source_message_ids=[],
            content=""
        )
        
        assert task.status == "completed"
        assert task.completed_at == datetime(2026, 3, 10, 9, 0)
        assert task.archived_at == archive_time

    def test_task_all_fields(self):
        """Проверить задачу со всеми полями"""
        created = datetime(2026, 3, 9, 10, 0)
        completed = datetime(2026, 3, 10, 9, 0)
        archived = datetime(2026, 3, 10, 2, 0)
        
        task = Task(
            id="task_004",
            title="Полная задача",
            tags=["work", "urgent"],
            status="completed",
            created_at=created,
            completed_at=completed,
            archived_at=archived,
            source_message_ids=["msg_001", "msg_002"],
            content="Тестовый контент задачи"
        )
        
        assert task.id == "task_004"
        assert task.title == "Полная задача"
        assert task.tags == ["work", "urgent"]
        assert task.status == "completed"
        assert task.created_at == created
        assert task.completed_at == completed
        assert task.archived_at == archived
        assert task.source_message_ids == ["msg_001", "msg_002"]
        assert task.content == "Тестовый контент задачи"

    def test_task_pending_no_completed_or_archived(self):
        """Проверить что pending задача не имеет completed_at и archived_at"""
        task = Task(
            id="task_005",
            title="Новая задача",
            tags=[],
            status="pending",
            created_at=datetime(2026, 3, 10, 10, 0),
            source_message_ids=["msg_001"],
            content="Контент"
        )
        
        assert task.status == "pending"
        assert task.completed_at is None
        assert task.archived_at is None