import asyncio
from aiogram import Router, F
<<<<<<< HEAD
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
=======
from aiogram.types import Message
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
from aiogram.filters import Command
import os

from bot.timers.manager import SummarizeTimer, summarizer_timer
from bot.db.file_manager import FileManager
from bot.config import settings
from bot.db.models import Task


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
Команды показываются в выводе /tasks под каждой задачей

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
    
    if len(parts) > 2 and parts[1] == "delay":
        try:
            delay_minutes = int(parts[2])
            delay_seconds = delay_minutes * 60
            
            if delay_minutes < 1:
                await message.answer("Задержка должна быть не менее 1 минуты")
                return
            
            # Сохранить в settings (в реальном проекте нужно сохранять в БД)
            settings.DEFAULT_SUMMARIZE_DELAY = delay_seconds
            
            # Сбросить текущий таймер для пользователя
            from bot.timers.manager import summarizer_timer
            await summarizer_timer.reset(message.from_user.id)
            
            # Запустить новый таймер с новой задержкой
            asyncio.create_task(summarizer_timer.schedule_summarization(message.from_user.id, delay_seconds))
            
            await message.answer(f"Задержка установлена на {delay_minutes} минут ({delay_seconds} секунд)")
            return
        except ValueError:
            await message.answer("Некорректное значение задержки. Используйте: /settings delay <минуты>")
            return
    else:
        current_delay_minutes = settings.DEFAULT_SUMMARIZE_DELAY // 60
        await message.answer(f"Текущая задержка: {current_delay_minutes} минут\nИспользуйте: /settings delay <минуты>")


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
    """Список задач с inline-кнопками"""
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    if not tasks:
        await message.answer("У вас пока нет задач")
        return
    
    # Собираем все задачи в одно сообщение
    response = "✅ Ваши задачи:\n\n"
<<<<<<< HEAD
    for i, task in enumerate(tasks):
=======
    for task in tasks:
        task_number = task.id.split("_")[1] if "_" in task.id else task.id
        
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
        status = "✅" if task.status == "completed" else "⏳"
        tags = ", ".join(task.tags) if task.tags else ""
        response += f"{status} {task.title} [{tags}]\n"
        response += f"   {task.content}\n"
        
        if task.status == "pending":
            response += f"   /done_{task_number}   /del_{task_number}\n"
        else:
            response += f"   /del_{task_number}\n"
        response += "\n"
    
    # Создаем клавиатуру для первой задачи
    first_task = tasks[0]
    status = "✅" if first_task.status == "completed" else "⏳"
    tags = ", ".join(first_task.tags) if first_task.tags else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Выполнено" if first_task.status == "pending" else "🔄 Отменить",
                callback_data=f"task_done:{first_task.id}"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"task_delete:{first_task.id}"
            ),
        ]
    ])
    
    await message.answer(
        response.rstrip(),
        reply_markup=keyboard
    )


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


<<<<<<< HEAD
@router.callback_query(F.data.startswith("task_done:"))
async def task_done_handler(callback: CallbackQuery):
    """
    Обработка нажатия кнопки выполнения задачи.
    
    Callback data: task_done:{task_id}
    Переключает статус задачи между pending и completed.
    Обновляет сообщение с задачей.
    """
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    new_status = "completed" if task.status == "pending" else "pending"
    success = file_manager.update_task_status(user_id, task_id, new_status)
    
    if success:
        status_icon = "✅" if new_status == "completed" else "⏳"
        action = "выполнена" if new_status == "completed" else "возвращена в список"
        await callback.answer(f"✅ Задача {action}!")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Отменить" if new_status == "completed" else "✅ Выполнено",
                    callback_data=f"task_done:{task_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"task_delete:{task_id}"
                ),
            ]
        ])
        
        tags = ", ".join(task.tags) if task.tags else ""
        await callback.message.edit_text(
            f"{status_icon} {task.title} [{tags}]\n"
            f"   {task.content}",
            reply_markup=keyboard
        )
    else:
        await callback.answer("❌ Ошибка при обновлении задачи", show_alert=True)


@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_handler(callback: CallbackQuery):
    """
    Обработка нажатия кнопки удаления задачи.
    
    Callback data: task_delete:{task_id}
    Запрашивает подтверждение удаления.
    """
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"task_delete_confirm:{task_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="task_delete_cancel"),
        ]
    ])
    
    await callback.answer(f"Удалить задачу \"{task.title}\"?", show_alert=True)
    await callback.message.edit_text(
        f"Удалить задачу:\n\n«{task.title}»\n{task.content}",
        reply_markup=confirm_keyboard
    )


@router.callback_query(F.data.startswith("task_delete_confirm:"))
async def task_delete_confirm_handler(callback: CallbackQuery):
    """
    Подтверждение удаления задачи.
    
    Callback data: task_delete_confirm:{task_id}
    Удаляет задачу и обновляет список.
    """
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
=======
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
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
    
    file_manager = FileManager()
    success = file_manager.delete_task(user_id, task_id)
    
    if success:
<<<<<<< HEAD
        await callback.answer("✅ Задача удалена!")
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при удалении задачи", show_alert=True)


@router.callback_query(F.data == "task_delete_cancel")
async def task_delete_cancel_handler(callback: CallbackQuery):
    """
    Отмена удаления задачи.
    
    Callback data: task_delete_cancel
    Возвращает к списку задач.
    """
    await callback.answer("❌ Удаление отменено")
    await callback.message.delete()
=======
        await message.answer(f"✅ Задача {task_number} удалена")
    else:
        await message.answer(f"❌ Задача {task_number} не найдена")
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
