from datetime import datetime
from typing import Optional

from aiogram import Bot

from bot.db.file_manager import FileManager
from bot.db.models import Task, Note
from utils.context_analyzer import ContextAnalyzer
from utils.ollama_client import OllamaClient


async def auto_summarize(user_id: int, bot: Optional[Bot] = None):
    """Автоматическая саммаризация сообщений пользователя"""
    file_manager = FileManager()
    
    messages = file_manager.read_messages(user_id)
    
    if not messages:
        if bot:
            try:
                await bot.send_message(
                    user_id, 
                    "♻️ Инбокс уже пуст"
                )
            except Exception:
                pass
        return
    
    try:
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        tasks_created = 0
        notes_created = 0
        skipped = 0
        report = []
        
        client = OllamaClient()
        
        for i, group in enumerate(groups, 1):
            result = await client.summarize_group(group)
            
            if result.get("action") == "create_task":
                task = Task(
                    id=f"task_{i:03d}",
                    title=result.get("title", f"Задача {i}"),
                    tags=result.get("tags", []),
                    content=result.get("content", ""),
                    source_message_ids=[m.id for m in group],
                    created_at=datetime.now()
                )
                file_manager.append_task(user_id, task)
                tasks_created += 1
                report.append(f"✅ Создана задача: {result.get('title', '')}")
            
            elif result.get("action") == "create_note":
                note = Note(
                    id=f"note_{i:03d}",
                    title=result.get("title", f"Заметка {i}"),
                    tags=result.get("tags", []),
                    content=result.get("content", ""),
                    source_message_ids=[m.id for m in group],
                    created_at=datetime.now()
                )
                file_manager.append_note(user_id, note)
                notes_created += 1
                report.append(f"📝 Создана заметка: {result.get('title', '')}")
            
            else:
                skipped += 1
                if group:
                    preview = group[0].content[:50] + "..." if group[0].content else "группа сообщений"
                    report.append(f"⏭ Пропущено: {preview}")
        
        file_manager.clear_messages(user_id)
        
        if bot:
            report_text = f"""♻️ Саммаризация завершена:

✅ Задачи создано: {tasks_created}
📝 Заметок создано: {notes_created}
⏭ Пропущено: {skipped}

""" + "\n".join(report)
            try:
                await bot.send_message(user_id, report_text.strip())
            except Exception:
                pass
        
        return {
            "tasks_created": tasks_created,
            "notes_created": notes_created,
            "skipped": skipped,
            "report": report
        }
        
    except Exception as e:
        if bot:
            try:
                await bot.send_message(
                    user_id, 
                    f"❌ Ошибка при саммаризации: {str(e)}"
                )
            except Exception:
                pass
        return {"error": str(e)}