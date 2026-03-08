from datetime import datetime
from typing import Optional
import logging

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.db.file_manager import FileManager
from bot.db.models import Task, Note
from utils.context_analyzer import ContextAnalyzer
from utils.ollama_client import OpenAIClient, OpenAIConfig

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("summarize"))
async def summarize_command(message: Message, bot: Bot):
    """Обработчик команды /summarize"""
    logger.debug(f"🔍 Команда /summarize получена от пользователя {message.from_user.id if message.from_user else 'unknown'}")
    if message.from_user is None:
        logger.warning("⚠️ message.from_user is None")
        return
    await message.answer("Запуск саммаризации...")
    logger.info(f"🚀 Запуск auto_summarize для пользователя {message.from_user.id}")
    await auto_summarize(message.from_user.id, bot)


async def auto_summarize(user_id: int, bot: Optional[Bot] = None):
    """Автоматическая саммаризация сообщений пользователя"""
    logger.info(f"📥 auto_summarize запущен для user_id={user_id}")
    file_manager = FileManager()
    
    messages = file_manager.read_messages(user_id)
    logger.info(f"📬 Прочитано сообщений из инбокса: {len(messages) if messages else 0}")
    if messages:
        for msg in messages[:3]:
            logger.debug(f"   - Сообщение: id={msg.id}, sender={msg.sender_name}, content_preview={msg.content[:50] if msg.content else 'empty'}...")
    
    if not messages:
        logger.warning("⚠️ Инбокс пуст! Нет сообщений для саммаризации")
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
        logger.info(f"🔧 Анализ контекста для {len(messages)} сообщений")
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        logger.info(f"📊 Создано групп для анализа: {len(groups)}")
        for i, group in enumerate(groups, 1):
            logger.debug(f"   Группа {i}: {len(group)} сообщений")
        
        tasks_created = 0
        notes_created = 0
        skipped = 0
        report = []
        
        client = OpenAIClient()
        
        for i, group in enumerate(groups, 1):
            logger.info(f"🔄 Обработка группы {i}/{len(groups)} ({len(group)} сообщений)")
            result = await client.summarize_group(group)
            logger.info(f"   → Результат: action={result.get('action')}, title={result.get('title', 'N/A')}")
            
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
        
        logger.info(f"💾 Сохранение backup перед очисткой инбокса")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"   Backup сохранен: {backup_path}")
        
        file_manager.clear_messages(user_id)
        logger.info(f"🗑️ Очистка инбокса выполнена")
        
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
        logger.error(f"❌ Ошибка при саммаризации: {e}")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"💾 Backup сохранен при ошибке: {backup_path}")
        if bot:
            try:
                await bot.send_message(
                    user_id, 
                    f"❌ Ошибка при саммаризации: {str(e)}\n\n📦 Ваши сообщения сохранены в backup"
                )
            except Exception:
                pass
        return {"error": str(e)}