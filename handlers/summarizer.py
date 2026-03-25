from datetime import datetime
from typing import Optional
import logging
import traceback

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.db.file_manager import FileManager
from bot.db.models import Task, Note
from utils.context_analyzer import ContextAnalyzer
from utils.ollama_client import OpenAIClient, OpenAIConfig
from utils.error_types import LLMTimeoutError, LLMNetworkError, LLMResponseError, LLMError

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("summarize"))
async def summarize_command(message: Message):
    """Обработчик команды /summarize"""
    logger.info(f"🔍 /summarize: user_id={message.from_user.id if message.from_user else 'None'}, text={message.text}, chat_id={message.chat.id}")
    if message.from_user is None:
        logger.warning("⚠️ message.from_user is None")
        return
    try:
        await message.answer("Запуск саммаризации...")
        logger.info(f"✅ Ответ отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке ответа: {e}")
    logger.info(f"🚀 Запуск auto_summarize для пользователя {message.from_user.id}")
    await auto_summarize(message.from_user.id, message.bot)


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
        
        if tasks_created > 0 or notes_created > 0:
            logger.info(f"💾 Сохранение backup перед очисткой инбокса")
            backup_path = file_manager.save_backup(user_id)
            logger.info(f"   Backup сохранен: {backup_path}")
            
            file_manager.clear_messages(user_id)
            logger.info(f"🗑️ Очистка инбокса выполнена")
        else:
            logger.warning(f"⚠️ Ничего не создано, инбокс не очищается")
        
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