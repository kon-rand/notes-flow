import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import os
import tempfile
from datetime import datetime

from bot.timers.manager import SummarizeTimer, summarizer_timer
from bot.db.file_manager import FileManager
from bot.config import settings
from bot.config.user_settings import user_settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Приветствие со статистикой"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    try:
        file_manager = FileManager()
        tasks = file_manager.read_tasks(user_id)
        notes = file_manager.read_notes(user_id)
        pending_tasks = [t for t in tasks if t.status == "pending"]
        
        stats = f"""🤖 Notes Flow

Привет! Я бот для управления задачами и заметками.

📊 Статистика:
✅ Задач создано: {len(tasks)}
📝 Заметок создано: {len(notes)}
⏳ Осталось задач: {len(pending_tasks)}

📌 Доступные команды:
/start - показать статистику
/inbox - просмотр инбокса
/tasks - список задач
/notes - список заметок
/summarize - ручная саммаризация
/settings delay <мин> - настройка задержки
/clear inbox - очистить инбокс
/archived - просмотр архивов
/archive - архивация задач
/help - показать эту справку"""
        
        await message.answer(stats)
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке статистики: {str(e)}")


@router.message(Command("help"))
async def help_handler(message: Message):
    """Показать список команд"""
    if message.from_user is None:
        return
    help_text = """📌 Доступные команды:

/start - показать статистику и приветствие
/inbox - просмотр текущего инбокса (последние 10 сообщений)
/tasks - список всех задач со статусами
/notes - список всех заметок
/summarize - ручная саммаризация инбокса
/settings delay <минуты> - настройка задержки саммаризации
/clear inbox - ручная очистка инбокса

💡 Управление задачами:
/done_XXX - отметить задачу как выполненную (XXX - номер задачи)
/del_XXX - удалить задачу (XXX - номер задачи)
/archived - просмотр архивов
/archive - архивация выполненных задач за сегодня

💡 Подсказки:
- Сообщения в инбоксе группируются автоматически
- Саммаризация запускается через {delay} минут после последнего сообщения
- Используйте /summarize для ручного запуска""".format(
        delay=settings.DEFAULT_SUMMARIZE_DELAY // 60
    )
    
    await message.answer(help_text)





@router.message(Command("settings"))
async def settings_handler(message: Message):
    """Настройка задержки саммаризации"""
    if message.from_user is None:
        return
    parts = message.text.split() if message.text else []
    
    user_id = message.from_user.id
    
    if len(parts) == 2:
        try:
            delay_minutes = int(parts[1])
            delay_seconds = delay_minutes * 60
            
            if delay_minutes < 1:
                await message.answer("Задержка должна быть не менее 1 минуты")
                return
            
            user_settings.set_delay(user_id, delay_seconds)
            await summarizer_timer.reset(user_id)
            asyncio.create_task(summarizer_timer.schedule_summarization(user_id, delay_seconds))
            await message.answer(f"Задержка установлена на {delay_minutes} минут ({delay_seconds} секунд)")
            return
        except ValueError:
            await message.answer("Некорректное значение задержки. Используйте: /settings <минуты>")
            return
    
    elif len(parts) > 2 and parts[1] == "delay":
        try:
            delay_minutes = int(parts[2])
            delay_seconds = delay_minutes * 60
            
            if delay_minutes < 1:
                await message.answer("Задержка должна быть не менее 1 минуты")
                return
            
            user_settings.set_delay(user_id, delay_seconds)
            await summarizer_timer.reset(user_id)
            asyncio.create_task(summarizer_timer.schedule_summarization(user_id, delay_seconds))
            await message.answer(f"Задержка установлена на {delay_minutes} минут ({delay_seconds} секунд)")
            return
        except ValueError:
            await message.answer("Некорректное значение задержки. Используйте: /settings <минуты>")
            return
    else:
        current_delay = user_settings.get_user_delay(user_id)
        current_delay_minutes = current_delay // 60
        await message.answer(f"Текущая задержка: {current_delay_minutes} минут\nИспользуйте: /settings <минуты>")


@router.message(Command("inbox"))
async def inbox_handler(message: Message):
    """Просмотр текущего инбокса"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    if not os.path.exists(f"data/{user_id}/inbox.md"):
        await message.answer("Инбокс пуст")
        return
    
    file_manager = FileManager()
    messages = file_manager.read_messages(user_id)
    
    if not messages:
        await message.answer("Инбокс пуст")
        return
    
    response = "📥 Ваш инбокс:\n\n"
    for msg in messages:
        response += f"• {msg.content}\n"
    
    await message.answer(response)


@router.message(Command("tasks"))
async def tasks_handler(message: Message):
    """Список задач"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    if not os.path.exists(f"data/{user_id}/tasks.md"):
        await message.answer("У вас пока нет задач")
        return
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    if not tasks:
        await message.answer("У вас пока нет задач")
        return
    
    response = "✅ Ваши задачи:\n\n"
    for task in tasks:
        task_number = task.id.split("_")[1] if "_" in task.id else task.id
        
        status = "✅" if task.status == "completed" else "⏳"
        tags = ", ".join(task.tags) if task.tags else ""
        response += f"{status} {task.title} [{tags}]\n"
        response += f"   {task.content}\n"
        
        if task.status == "pending":
            response += f"   /done_{task_number}   /del_{task_number}\n"
        else:
            response += f"   /del_{task_number}\n"
        response += "\n"
    
    await message.answer(response)


@router.message(Command("notes"))
async def notes_handler(message: Message):
    """Список заметок"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    if not os.path.exists(f"data/{user_id}/notes.md"):
        await message.answer("У вас пока нет заметок")
        return
    
    file_manager = FileManager()
    notes = file_manager.read_notes(user_id)
    
    if not notes:
        await message.answer("У вас пока нет заметок")
        return
    
    response = "📝 Ваши заметки:\n\n"
    for note in notes:
        tags = ", ".join(note.tags) if note.tags else ""
        response += f"• {note.title} [{tags}]\n"
        response += f"  {note.content}\n\n"
    
    await message.answer(response)


@router.message(Command("clear"))
async def clear_handler(message: Message):
    """Очистка инбокса"""
    if message.from_user is None:
        return
    parts = message.text.split() if message.text else []
    
    if len(parts) < 2 or parts[1] != "inbox":
        await message.answer("Используйте: /clear inbox")
        return
    
    user_id = message.from_user.id
    
    # Сбросить таймер
    await summarizer_timer.reset(user_id)
    
    # Очистить инбокс
    file_manager = FileManager()
    file_manager.clear_messages(user_id)
    
    await message.answer("Инбокс очищен")


@router.message(F.text.startswith("/done_"))
async def done_task_handler(message: Message):
    """Отметить задачу как выполненную"""
    if message.from_user is None:
        return
    
    task_number = message.text[6:]
    if not task_number.isdigit():
        await message.answer("❌ Неверный формат команды. Используйте: /done_123")
        return
    
    task_id = f"task_{task_number.zfill(3)}"
    user_id = message.from_user.id
    
    file_manager = FileManager()
    success = file_manager.update_task_status(user_id, task_id, "completed")
    
    if success:
        await message.answer(f"✅ Задача {task_number} отмечена как выполненная")
    else:
        await message.answer(f"❌ Задача {task_number} не найдена")


@router.message(F.text.startswith("/del_"))
async def delete_task_handler(message: Message):
    """Удалить задачу"""
    if message.from_user is None:
        return
    
    task_number = message.text[5:]
    if not task_number.isdigit():
        await message.answer("❌ Неверный формат команды. Используйте: /del_123")
        return
    
    task_id = f"task_{task_number.zfill(3)}"
    user_id = message.from_user.id
    
    file_manager = FileManager()
    success = file_manager.delete_task(user_id, task_id)
    
    if success:
        await message.answer(f"✅ Задача {task_number} удалена")
    else:
        await message.answer(f"❌ Задача {task_number} не найдена")


@router.message(Command("archived"))
async def archived_handler(message: Message):
    """Показать список дат с архивом или задачи за дату"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    parts = message.text.split()
    
    if len(parts) == 1:
        file_manager = FileManager()
        archive_dates = file_manager.get_archive_dates(user_id)
        
        if not archive_dates:
            await message.answer("У вас пока нет архивов")
            return
        
        response = "📁 Архивы задач:\n\n"
        for date in archive_dates:
            tasks = file_manager.get_tasks_by_archive_date(user_id, date)
            task_count = len(tasks)
            date_navigate = date.replace("-", "_")
            response += f"📅 /{date_navigate} ({task_count} задач)\n"
        
        await message.answer(response)
    else:
        date_input = parts[1]
        
        if not date_input.replace("_", "").isdigit():
            await message.answer("❌ Неверный формат даты. Используйте: /archived YYYY_MM_DD")
            return
        
        date_display = date_input.replace("_", "-")
        
        file_manager = FileManager()
        tasks = file_manager.get_tasks_by_archive_date(user_id, date_input)
        
        if not tasks:
            await message.answer(f"Задач за {date_display} не найдено")
            return
        
        response = f"✅ Задачи за {date_display}:\n\n"
        for task in tasks:
            tags = ", ".join(task.tags) if task.tags else ""
            response += f"📌 {task.title} [{tags}]\n"
            response += f"   {task.content}\n\n"
        
        await message.answer(response)
        



archive_router = Router()

@archive_router.message(F.text.startswith("/"))
async def archive_date_handler(message: Message):
    if message.from_user is None:
        return
    
    logger.info(f"🔍 archive_date_handler: text={message.text}, user_id={message.from_user.id}")
    
    # Игнорируем команды, которые обрабатываются другими хендлерами
    if message.text in ["/summarize", "/start", "/help", "/settings", "/inbox", "/tasks", "/notes", "/clear", "/archive", "/archived"]:
        logger.info(f"   → Skipping command {message.text} (handled by other handler)")
        return
    
    date_input = message.text[1:]
    
    if not date_input.replace("_", "").replace("-", "").isdigit() or len(date_input) != 10:
        logger.info(f"   → Invalid date format: '{date_input}'")
        return
    
    try:
        if "_" in date_input:
            year, month, day = date_input.split("_")
        elif "-" in date_input:
            year, month, day = date_input.split("-")
        else:
            logger.info(f"   → No separator found")
            return
        
        datetime(int(year), int(month), int(day))
    except (ValueError, TypeError):
        logger.info(f"   → Invalid date values")
        return
    
    date_display = f"{year}-{month}-{day}"
    date_file = date_display
    
    file_manager = FileManager()
    tasks = file_manager.get_tasks_by_archive_date(message.from_user.id, date_file)
    
    if not tasks:
        await message.answer(f"Задач за {date_display} не найдено")
        return
    
    response = f"✅ Задачи за {date_display}:\n\n"
    for task in tasks:
        tags = ", ".join(task.tags) if task.tags else ""
        response += f"📌 {task.title} [{tags}]\n"
        response += f"   {task.content}\n\n"
    
    await message.answer(response)


@router.message(Command("archive"))
async def archive_handler(message: Message):
    """Архивация выполненных задач за сегодня"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    today = datetime.now()
    file_manager = FileManager()
    archived_tasks = file_manager.archive_completed_tasks(user_id, today)
    
    await message.answer(f"✅ Архивировано задач за {today.strftime('%Y-%m-%d')}: {len(archived_tasks)}")

@router.message(Command("backup"))
async def backup_handler(message: Message):
    if message.from_user is None:
        return
    
    user_id = message.from_user.id
    
    try:
        file_manager = FileManager()
        backup_file = file_manager.create_backup(user_id)
        
        if backup_file is None:
            await message.answer("Нет данных для бэкапа")
            return
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_file.write(backup_file.getvalue())
        temp_file.close()
        
        await message.answer_document(
            document=FSInputFile(temp_file.name),
            filename="backup.zip"
        )
        
        os.unlink(temp_file.name)
        
        logger.info(f"Backup created for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error creating backup for user {user_id}: {e}")
        await message.answer(f"❌ Ошибка при создании бэкапа: {str(e)}")