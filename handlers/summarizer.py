import asyncio
from typing import List
from datetime import datetime

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage, Task, Note
from bot.config import settings


async def auto_summarize(user_id: int):
    """Автоматическая саммаризация сообщений пользователя"""
    file_manager = FileManager()
    
    # Чтение сообщений из инбокса
    messages = file_manager.read_messages(user_id)
    
    if not messages:
        return
    
    # Здесь должна быть группировка сообщений (ContextAnalyzer)
    # Для простоты пока объединяем все сообщения в одну группу
    groups = [messages]
    
    created_items = []
    
    for group in groups:
        if not group:
            continue
        
        # Здесь должен быть вызов OllamaClient для анализа
        # Для простоты пока создаём заметку
        source_ids = [msg.id for msg in group]
        content_text = "\n".join(msg.content for msg in group)
        
        # Создаём заметку (вместо анализа через AI)
        note = Note(
            id=f"auto_{datetime.now().timestamp()}",
            title=f"Автоматическая саммаризация {datetime.now().strftime('%H:%M')}",
            tags=["auto"],
            created_at=datetime.now(),
            source_message_ids=source_ids,
            content=content_text,
        )
        
        file_manager.append_note(user_id, note)
        created_items.append(f"note:{note.id}")
    
    # Очистка инбокса
    file_manager.clear_messages(user_id)
    
    # Отправка отчёта (в реальном проекте)
    # await bot.send_message(user_id, f"Создано {len(created_items)} элементов")
    
    return created_items