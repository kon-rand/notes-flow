# TICKET-007: Команды бота

## Описание задачи
Реализовать все команды бота для ручного управления: /start, /summarize, /inbox, /tasks, /notes, /settings, /clear.

## Компоненты для реализации
- `handlers/commands.py` - обработка всех команд бота

## Приоритет
🟡 Высокий

## Критерии приёмки
- [ ] /start - приветствие со статистикой
- [ ] /summarize - ручной запуск саммаризации
- [ ] /inbox - просмотр текущего инбокса
- [ ] /tasks - список задач со статусами
- [ ] /task done <id> - отметить задачу выполненной
- [ ] /notes - список заметок
- [ ] /settings delay <minutes> - настройка задержки
- [ ] /clear inbox - ручная очистка инбокса
- [ ] Все команды возвращают читаемые отчёты

## Технические детали

### handlers/commands.py
```python
from aiogram import dp, types
from aiogram.filters import Command
from pydantic import BaseModel

# Команда /start
@dp.message_handler(Command("start"))
async def start_handler(message: types.Message):
    """Приветствие со статистикой"""
    user_id = message.from_user.id
    
    # Статистика
    tasks = FileManager.read_tasks(user_id)
    notes = FileManager.read_notes(user_id)
    pending_tasks = [t for t in tasks if t.status == "pending"]
    
    stats = f"""
🤖 Бот Notes Flow

Статистика:
✅ Задач создано: {len(tasks)}
📝 Заметок создано: {len(notes)}
⏳ Осталось задач: {len(pending_tasks)}

Команды:
/start - показать статистику
/summarize - ручная саммаризация
/inbox - просмотр инбокса
/tasks - список задач
/task done <id> - выполнить задачу
/notes - список заметок
/settings delay <мин> - настройка задержки
/clear inbox - очистить инбокс
"""
    
    await message.answer(stats.strip())

# Команда /summarize
@dp.message_handler(Command("summarize"))
async def summarize_handler(message: types.Message):
    """Ручной запуск саммаризации"""
    user_id = message.from_user.id
    
    # Сбросить таймер
    SummarizeTimer.reset(user_id)
    
    await message.answer("♻️ Запуск саммаризации...")
    await auto_summarize(user_id)

# Команда /inbox
@dp.message_handler(Command("inbox"))
async def inbox_handler(message: types.Message):
    """Просмотр текущего инбокса"""
    user_id = message.from_user.id
    
    messages = FileManager.read_messages(user_id)
    
    if not messages:
        await message.answer("📥 Инбокс пуст")
        return
    
    report = "📥 Ваши сообщения:\n\n"
    for msg in messages:
        sender = msg.sender_name or f"User {msg.sender_id}"
        report += f"• [{msg.timestamp.strftime('%H:%M')}] {sender}: {msg.content}\n\n"
    
    await message.answer(report)

# Команда /tasks
@dp.message_handler(Command("tasks"))
async def tasks_handler(message: types.Message):
    """Список задач"""
    user_id = message.from_user.id
    
    tasks = FileManager.read_tasks(user_id)
    
    if not tasks:
        await message.answer("✅ Нет задач")
        return
    
    report = "✅ Ваши задачи:\n\n"
    for task in tasks:
        status = "✓" if task.status == "completed" else "⏳"
        tags = ", ".join(task.tags) if task.tags else ""
        report += f"{status} [{task.id}] {task.title}"
        if tags:
            report += f" #{tags}"
        report += "\n"
    
    await message.answer(report)

# Команда /task done
@dp.message_handler(commands=["task"])
async def task_done_handler(message: types.Message):
    """Отметить задачу выполненной"""
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) < 3 or parts[1] != "done":
        await message.answer("Используйте: /task done <id>")
        return
    
    task_id = parts[2]
    FileManager.update_task_status(task_id, "completed")
    
    await message.answer(f"✅ Задача {task_id} выполнена")

# Команда /notes
@dp.message_handler(Command("notes"))
async def notes_handler(message: types.Message):
    """Список заметок"""
    user_id = message.from_user.id
    
    notes = FileManager.read_notes(user_id)
    
    if not notes:
        await message.answer("📝 Нет заметок")
        return
    
    report = "📝 Ваши заметки:\n\n"
    for note in notes:
        tags = ", ".join(note.tags) if note.tags else ""
        report += f"• [{note.id}] {note.title}"
        if tags:
            report += f" #{tags}"
        report += f"\n  {note.content[:100]}...\n\n"
    
    await message.answer(report)

# Команда /settings
@dp.message_handler(commands=["settings"])
async def settings_handler(message: types.Message):
    """Настройка задержки саммаризации"""
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) > 2:
        delay_minutes = int(parts[2])
        delay_seconds = delay_minutes * 60
        
        # Сохранить настройку
        Settings.DEFAULT_SUMMARIZE_DELAY = delay_seconds
        
        # Обновить таймер
        SummarizeTimer.schedule_summarization(user_id, delay_seconds)
        
        await message.answer(f"⏱ Задержка установлена на {delay_minutes} минут")
    else:
        await message.answer("Используйте: /settings delay <минуты>")

# Команда /clear
@dp.message_handler(commands=["clear"])
async def clear_handler(message: types.Message):
    """Очистка инбокса вручную"""
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) > 1 and parts[1] == "inbox":
        FileManager.clear_messages(user_id)
        await message.answer("🗑 Инбокс очищен")
    else:
        await message.answer("Используйте: /clear inbox")
```