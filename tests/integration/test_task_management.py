import pytest
from pathlib import Path
from bot.db.file_manager import FileManager
from bot.db.models import Task
from datetime import datetime


class TestTaskInlineActions:
    @pytest.fixture
    def file_manager(self, tmp_path):
        """Создать тестовый FileManager"""
        return FileManager(data_dir=str(tmp_path))
    
    @pytest.fixture
    def user_id(self):
        return 999999
    
    def test_complete_task(self, file_manager, user_id):
        """Тест выполнения задачи через FileManager"""
        task = Task(
            id="task_001",
            title="Test Task",
            tags=["test"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Test content"
        )
        file_manager.append_task(user_id, task)
        
        success = file_manager.update_task_status(user_id, "task_001", "completed")
        assert success is True
        
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].status == "completed"
    
    def test_delete_task(self, file_manager, user_id):
        """Тест удаления задачи"""
        task = Task(
            id="task_002",
            title="To Delete",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 1
        task_id = tasks[0].id
        
        success = file_manager.delete_task(user_id, task_id)
        assert success is True
        
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 0
    
    def test_toggle_task_status(self, file_manager, user_id):
        """Тест переключения статуса задачи"""
        task = Task(
            id="task_003",
            title="Toggle Test",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        tasks = file_manager.read_tasks(user_id)
        task_id = tasks[0].id
        
        file_manager.update_task_status(user_id, task_id, "completed")
        tasks = file_manager.read_tasks(user_id)
        assert tasks[0].status == "completed"
        
        file_manager.update_task_status(user_id, task_id, "pending")
        tasks = file_manager.read_tasks(user_id)
        assert tasks[0].status == "pending"
    
    def test_delete_last_task_removes_file(self, file_manager, user_id):
        """Тест удаления последней задачи удаляет файл"""
        task = Task(
            id="task_004",
            title="Last Task",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        tasks = file_manager.read_tasks(user_id)
        task_id = tasks[0].id
        file_manager.delete_task(user_id, task_id)
        
        task_path = Path(file_manager._get_user_dir(user_id)) / "tasks.md"
        assert not task_path.exists()
    
    def test_delete_nonexistent_task(self, file_manager, user_id):
        """Тест удаления несуществующей задачи"""
        task = Task(
            id="task_005",
            title="Test Task",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        success = file_manager.delete_task(user_id, "task_nonexistent")
        assert success is True
        
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].title == "Test Task"
    
    def test_multiple_tasks_delete_one(self, file_manager, user_id):
        """Тест удаления одной задачи из нескольких"""
        task1 = Task(
            id="task_006",
            title="Task 1",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        task2 = Task(
            id="task_007",
            title="Task 2",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task1)
        file_manager.append_task(user_id, task2)
        
        tasks = file_manager.read_tasks(user_id)
        task1_id = tasks[0].id
        file_manager.delete_task(user_id, task1_id)
        
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].title == "Task 2"