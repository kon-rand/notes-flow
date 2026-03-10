# TICKET-015: Управление задачами (выполнение и удаление)

## Описание
Реализовать возможность отмечать задачи как выполненные и удалять их через динамические команды `/done_{task_id}` и `/del_{task_id}`.

## Приоритет
🟡 средний

## Компоненты для реализации

### 1. Модификация `bot/db/file_manager.py`
**Добавить метод `delete_task()`:**

```python
def delete_task(self, user_id: int, task_id: str) -> bool:
    """Удалить задачу по ID. Возвращает True при успехе."""
    items = self._load_all_items(user_id, "tasks")
    items = [(id, data) for id, data in items if id != task_id]
    
    if len(items) == 0:
        # Если задач больше нет, удалить файл
        tasks_path = self._get_user_dir(user_id) / "tasks.md"
        if tasks_path.exists():
            tasks_path.unlink()
        return True
    
    file_path = self._get_user_dir(user_id) / "tasks.md"
    self._write_file(file_path, "task", items)
    return True
```

### 2. Модификация `handlers/commands.py`
**Добавить динамические обработчики команд:**

```python
from aiogram import F  # Добавить в импорты

@router.message(F.text.startswith("/done_"))
async def done_task_handler(message: Message):
    """Отметить задачу как выполненную"""
    if message.from_user is None:
        return
    
    task_number = message.text[6:]  # Извлечь номер после "/done_"
    if not task_number.isdigit():
        await message.answer("❌ Неверный формат команды. Используйте: /done_123")
        return
    
    task_id = f"task_{task_number.zfill(3)}"  # Преобразовать в "task_123"
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
    
    task_number = message.text[5:]  # Извлечь номер после "/del_"
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
```

### 3. Обновление вывода `/tasks`
**Модифицировать `tasks_handler`:**

```python
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
        # Извлечь номер задачи из ID (task_001 -> 001)
        task_number = task.id.split("_")[1] if "_" in task.id else task.id
        
        status = "✅" if task.status == "completed" else "⏳"
        tags = ", ".join(task.tags) if task.tags else ""
        response += f"{status} {task.title} [{tags}]\n"
        response += f"   {task.content}\n"
        
        # Добавить команды управления
        if task.status == "pending":
            response += f"   /done_{task_number}   /del_{task_number}\n"
        else:
            response += f"   /del_{task_number}\n"
        response += "\n"
    
    await message.answer(response)
```

### 4. Обновление справки `/help`
**Добавить в `help_handler`:**

```python
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
Команды показываются в выводе /tasks под каждой задачей"""
```

### 5. Тестирование

**Тесты для `file_manager.py`** (`tests/unit/db/test_file_manager.py`):
```python
def test_delete_task_success(tmp_path, sample_user_id):
    """Тест успешного удаления задачи"""
    fm = FileManager(str(tmp_path))
    
    # Создать тестовую задачу
    task = Task(
        id="task_001",
        title="Тестовая задача",
        tags=["тест"],
        status="pending",
        created_at=datetime.now(),
        source_message_ids=[],
        content="Тест"
    )
    fm.append_task(sample_user_id, task)
    
    # Удалить задачу
    result = fm.delete_task(sample_user_id, "task_001")
    
    assert result is True
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 0


def test_delete_task_not_found(tmp_path, sample_user_id):
    """Тест удаления несуществующей задачи"""
    fm = FileManager(str(tmp_path))
    
    result = fm.delete_task(sample_user_id, "task_999")
    
    assert result is False


def test_delete_task_preserves_others(tmp_path, sample_user_id):
    """Тест что удаление одной задачи не затрагивает другие"""
    fm = FileManager(str(tmp_path))
    
    task1 = Task(id="task_001", title="Задача 1", tags=[], 
                 status="pending", created_at=datetime.now(), 
                 source_message_ids=[], content="1")
    task2 = Task(id="task_002", title="Задача 2", tags=[], 
                 status="pending", created_at=datetime.now(), 
                 source_message_ids=[], content="2")
    fm.append_task(sample_user_id, task1)
    fm.append_task(sample_user_id, task2)
    
    fm.delete_task(sample_user_id, "task_001")
    
    tasks = fm.read_tasks(sample_user_id)
    assert len(tasks) == 1
    assert tasks[0].id == "task_002"
```

**Тесты для команд** (`tests/unit/handlers/test_commands.py`):
```python
@pytest.mark.asyncio
async def test_done_task_success(mock_message, mock_file_manager):
    """Тест команды /done_XXX"""
    mock_message.text = "/done_001"
    mock_message.from_user.id = 123
    
    mock_file_manager.update_task_status.return_value = True
    
    from handlers.commands import done_task_handler
    await done_task_handler(mock_message)
    
    mock_file_manager.update_task_status.assert_called_once_with(123, "task_001", "completed")


@pytest.mark.asyncio
async def test_done_task_invalid_format(mock_message, mock_file_manager):
    """Тест команды с неверным форматом"""
    mock_message.text = "/done_abc"
    
    from handlers.commands import done_task_handler
    await done_task_handler(mock_message)
    
    mock_file_manager.update_task_status.assert_not_called()


@pytest.mark.asyncio
async def test_delete_task_success(mock_message, mock_file_manager):
    """Тест команды /del_XXX"""
    mock_message.text = "/del_001"
    mock_message.from_user.id = 123
    
    mock_file_manager.delete_task.return_value = True
    
    from handlers.commands import delete_task_handler
    await delete_task_handler(mock_message)
    
    mock_file_manager.delete_task.assert_called_once_with(123, "task_001")
```

## Технические детали
- Task ID имеют формат `task_XXX` (например, `task_001`)
- Пользователь вводит только номер (например, `/done_123`)
- Нужно преобразовывать номер в формат `task_XXX` с добавлением ведущего нуля
- Для pending задач показывать обе команды: `/done_XXX` и `/del_XXX`
- Для completed задач показывать только `/del_XXX`

## Требования к тестированию
1. Тесты метода `delete_task()` в `file_manager`
2. Тесты динамических обработчиков команд
3. Тест корректного форматирования task_id
4. Тест обработки некорректных входных данных
5. Интеграционный тест: создание задачи → выполнение → удаление

## Обновление документации
- ✅ Обновить `/help` с описанием новых команд
- ✅ Обновить вывод `/tasks` с примерами команд
- ✅ Обновить README.md (если есть раздел с описанием команд)