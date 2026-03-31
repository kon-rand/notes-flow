from datetime import datetime
from typing import Optional
import logging
import traceback

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.db.file_manager import FileManager
from bot.db.models import Task, Note
from utils.ollama_client import OpenAIClient, OpenAIConfig
from utils.error_types import LLMTimeoutError, LLMNetworkError, LLMResponseError, LLMError
from bot.helpers.message_updater import update_or_create_task_message

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("summarize"))
async def summarize_command(message: Message):
    """Обработчик команды /summarize"""
    logger.info(f"🔍 /summarize: user_id={message.from_user.id if message.from_user else 'None'}, text={message.text}, chat_id={message.chat.id}")
    if message.from_user is None:
        logger.warning("⚠️ message.from_user is None")
        return
    
    user_name = message.from_user.full_name if message.from_user else None
    
    # Cancel any pending auto-summarization timer and run immediate summarization
    from bot.timers.manager import summarizer_timer
    await summarizer_timer.trigger_immediate_summarization(
        user_id=message.from_user.id,
        bot=message.bot,
        user_name=user_name,
        trigger_backup=False  # Manual summarization does NOT trigger backup
    )


async def auto_summarize(user_id: int, bot: Optional[Bot] = None, trigger_backup: bool = True):
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
        logger.info(f"🔧 Анализ {len(messages)} сообщений через LLM")
        
        tasks_created = 0
        notes_created = 0
        skipped = 0
        report = []
        
        created_tasks = []
        created_notes = []
        
        client = OpenAIClient()
        # LLM сам определяет группировку и возвращает список всех задач
        results = await client.summarize_messages(messages)
        logger.info(f"📊 LLM вернул {len(results)} задач/заметок")
        
        for i, result in enumerate(results, 1):
            logger.info(f"   [{i}] action={result.get('action')}, title={result.get('title', 'N/A')}")
            
            if result.get("action") == "create_task":
                # Берём все source_message_ids из результата или создаём новые
                source_ids = result.get("source_message_ids", [m.id for m in messages])
                task = Task(
                    id=f"task_{i:03d}",
                    title=result.get("title", f"Задача {i}"),
                    tags=result.get("tags", []),
                    content=result.get("content", ""),
                    source_message_ids=source_ids,
                    created_at=datetime.now()
                )
                file_manager.append_task(user_id, task)
                tasks_created += 1
                report.append(f"✅ Создана задача: {result.get('title', '')}")
                created_tasks.append(task)
            
            elif result.get("action") == "create_note":
                source_ids = result.get("source_message_ids", [m.id for m in messages])
                note = Note(
                    id=f"note_{i:03d}",
                    title=result.get("title", f"Заметка {i}"),
                    tags=result.get("tags", []),
                    content=result.get("content", ""),
                    source_message_ids=source_ids,
                    created_at=datetime.now()
                )
                file_manager.append_note(user_id, note)
                notes_created += 1
                report.append(f"📝 Создана заметка: {result.get('title', '')}")
                created_notes.append(note)
            
            else:
                skipped += 1
        
        if tasks_created > 0 or notes_created > 0:
            logger.info(f"💾 Сохранение backup перед очисткой инбокса")
            backup_path = file_manager.save_backup(user_id)
            logger.info(f"   Backup сохранен: {backup_path}")
            
            file_manager.clear_messages(user_id)
            logger.info(f"🗑️ Очистка инбокса выполнена")
        else:
            logger.warning(f"⚠️ Ничего не создано, инбокс не очищается")
     
        if bot:
            report_lines = [
                "✅ Саммаризация завершена",
                "",
                "Создано:",
                f"- Задач: {tasks_created}",
                f"- Заметок: {notes_created}",
                ""
            ]
            
            if created_tasks:
                report_lines.append("Созданные задачи:")
                for i, task in enumerate(created_tasks[:10]):
                    tags_str = ", ".join(task.tags) if task.tags else "нет тегов"
                    report_lines.append(f"• {task.title} (tags: {tags_str})")
            
            if created_notes:
                report_lines.append("Созданные заметки:")
                for i, note in enumerate(created_notes[:10]):
                    report_lines.append(f"• {note.title}")
            
            total_items = tasks_created + notes_created
            if total_items > 10:
                report_lines.append("")
                report_lines.append("Показать все: используйте /tasks и /notes")
            
            report_lines.append("")
            report_lines.append("Используйте /tasks для просмотра задач, /notes для просмотра заметок")
            
            report_text = "\n".join(report_lines)
            
            try:
                await bot.send_message(user_id, report_text.strip())
            except Exception:
                pass
        
        # Обновляем /tasks после саммаризации
        if bot:
            try:
                from bot.helpers.message_updater import update_or_create_task_message
                # Создаём временное сообщение для вызова update
                temp_msg = type('obj', (object,), {
                    'from_user': type('obj', (object,), {'id': user_id})(),
                    'chat': type('obj', (object,), {'id': user_id})(),
                    'bot': bot,
                    'text': None
                })()
                await update_or_create_task_message(temp_msg, "✅ Саммаризация завершена")
            except Exception as e:
                logger.warning(f"Failed to update /tasks after summarization: {e}")
        
        return {
            "tasks_created": tasks_created,
            "notes_created": notes_created,
            "skipped": skipped,
            "report": report
        }
        
    except LLMTimeoutError as e:
        logger.error(f"❌ Таймаут LLM: {str(e)}")
        logger.error(f"   Stack:\n{traceback.format_exc()}")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"💾 Backup сохранен при ошибке: {backup_path}")
        if bot:
            try:
                await bot.send_message(
                    user_id,
                    "❌ Таймаут при обращении к LLM\n\n"
                    "💡 Ваши сообщения сохранены и будут обработаны позже.\n"
                    "🔄 Попробуйте /summarize снова через 5-10 минут."
                )
            except Exception:
                pass
        return {"error": "timeout", "message": str(e)}
    
    except LLMNetworkError as e:
        logger.error(f"❌ Сетевая ошибка LLM: {str(e)}")
        logger.error(f"   Stack:\n{traceback.format_exc()}")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"💾 Backup сохранен при ошибке: {backup_path}")
        if bot:
            try:
                await bot.send_message(
                    user_id,
                    "❌ Сетевая ошибка при обращении к LLM\n\n"
                    "💡 Проверьте соединение и попробуйте снова."
                )
            except Exception:
                pass
        return {"error": "network", "message": str(e)}
    
    except LLMResponseError as e:
        logger.error(f"❌ Ошибка ответа LLM: {str(e)}")
        logger.error(f"   Stack:\n{traceback.format_exc()}")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"💾 Backup сохранен при ошибке: {backup_path}")
        if bot:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Ошибка ответа от LLM: {str(e)}\n\n"
                    "💡 Ваши сообщения сохранены.\n"
                    "🔄 Попробуйте /summarize снова."
                )
            except Exception:
                pass
        return {"error": "response", "message": str(e)}
    
    except LLMError as e:
        logger.error(f"❌ Ошибка LLM: {str(e)}")
        logger.error(f"   Stack:\n{traceback.format_exc()}")
        backup_path = file_manager.save_backup(user_id)
        logger.info(f"💾 Backup сохранен при ошибке: {backup_path}")
        if bot:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Ошибка: {str(e)}\n\n"
                    "💡 Ваши сообщения сохранены.\n"
                    "🔄 Попробуйте /summarize снова."
                )
            except Exception:
                pass
        return {"error": "unknown", "message": str(e)}