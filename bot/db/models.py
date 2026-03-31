from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class InboxMessage(BaseModel):
    id: str
    timestamp: datetime
    from_user: int
    sender_id: int
    sender_name: Optional[str]
    content: str
    chat_id: int


class Task(BaseModel):
    id: str
    title: str
    tags: List[str]
    status: str = "pending"
    created_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    source_message_ids: List[str]
    content: str


class Note(BaseModel):
    id: str
    title: str
    tags: List[str]
    created_at: datetime
    source_message_ids: List[str]
    content: str


class UserSettings(BaseModel):
    """Настройки пользователя с сохранением последнего использованного ID"""
    delay: int  # Задержка саммаризации в секундах
    last_task_id: int = 0  # Последний использованный номер задачи
    last_note_id: int = 0  # Последний использованный номер заметки
    last_message_id: int = 0  # Последний использованный номер сообщения
    tasks_message_id: Optional[int] = None  # ID последнего сообщения /tasks
    archive_message_id: Optional[int] = None  # ID последнего сообщения /archive