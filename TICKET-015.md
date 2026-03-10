<<<<<<< HEAD
# TICKET-015: Inline-кнопки для управления задачами
=======
# TICKET-015: Управление задачами (выполнение и удаление)
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)

## Описание
Реализовать возможность отмечать задачи как выполненные и удалять их через динамические команды `/done_{task_id}` и `/del_{task_id}`.

<<<<<<< HEAD
Добавить inline-кнопки в список задач для быстрого выполнения и удаления задач без ввода ID.

## Цель

Упростить управление задачами через Telegram бота:
- ⏳ **Выполнение задачи** — одна кнопка вместо команды `/task done <id>`
- 🗑 **Удаление задачи** — одна кнопка вместо удаления через файл
- Не нужно запоминать или копировать ID задач

## Требования

### 1. Модификация команды `/tasks`

**Файл**: `handlers/commands.py`

Изменить `tasks_handler` для добавления inline-кнопок к каждой задаче:

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    
    # Формирование списка с кнопками
    for task in tasks:
        status = "✅" if task.status == "completed" else "⏳"
        tags = ", ".join(task.tags) if task.tags else ""
        
        # Создать клавиатуру для задачи
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено" if task.status == "pending" else "🔄 Отменить",
                    callback_data=f"task_done:{task.id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"task_delete:{task.id}"
                ),
            ]
        ])
        
        await message.answer(
            f"{status} {task.title} [{tags}]\n"
            f"   {task.content}",
            reply_markup=keyboard
        )
```

### 2. Обработчики callback queries

**Файл**: `handlers/commands.py` (добавить новые обработчики)

#### Обработка выполнения/отмены задачи:

```python
@router.callback_query(F.data.startswith("task_done:"))
async def task_done_handler(callback: CallbackQuery):
    """Выполнение или отмена выполнения задачи"""
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    # Найти задачу
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    # Переключить статус
    new_status = "completed" if task.status == "pending" else "pending"
    success = file_manager.update_task_status(user_id, task_id, new_status)
    
    if success:
        status_icon = "✅" if new_status == "completed" else "⏳"
        action = "выполнена" if new_status == "completed" else "возвращена в список"
        await callback.answer(f"✅ Задача {action}!")
        
        # Обновить сообщение
        await callback.message.edit_text(
            f"{status_icon} {task.title} [{', '.join(task.tags)}]\n"
            f"   {task.content}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
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
        )
    else:
        await callback.answer("❌ Ошибка при обновлении задачи", show_alert=True)
```

#### Обработка удаления задачи:

```python
@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_handler(callback: CallbackQuery):
    """Удаление задачи"""
    from aiogram import F
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    file_manager = FileManager()
    tasks = file_manager.read_tasks(user_id)
    
    # Найти задачу
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    # Подтверждение удаления
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
```

#### Подтверждение удаления:

```python
@router.callback_query(F.data.startswith("task_delete_confirm:"))
async def task_delete_confirm_handler(callback: CallbackQuery):
    """Подтверждение удаления задачи"""
    from aiogram import F
    task_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Удаление задачи через FileManager
    # TODO: добавить метод delete_task в FileManager
    file_manager = FileManager()
    # file_manager.delete_task(user_id, task_id)
    
    await callback.answer("✅ Задача удалена!")
    await callback.message.delete()
    
    # Показать обновленный список задач
    await tasks_handler(callback.message)
```

#### Отмена удаления:

```python
@router.callback_query(F.data == "task_delete_cancel")
async def task_delete_cancel_handler(callback: CallbackQuery):
    """Отмена удаления задачи"""
    await callback.answer("❌ Удаление отменено")
    await callback.message.delete()
    await tasks_handler(callback.message)
```

### 3. Метод удаления в FileManager

**Файл**: `bot/db/file_manager.py`

Добавить метод `delete_task`:

```python
def delete_task(self, user_id: int, task_id: str) -> bool:
    """Удалить задачу по ID"""
    items = self._load_all_items(user_id, "tasks")
    
    # Найти и удалить задачу
    items = [(id, data) for id, data in items if id != task_id]
    
    if len(items) == 0:
        # Если задач нет, удалить файл
        task_path = self._get_user_dir(user_id) / "tasks.md"
        if task_path.exists():
            task_path.unlink()
    else:
        # Обновить файл
        file_path = self._get_user_dir(user_id) / "tasks.md"
        self._write_file(file_path, "task", items)
    
    return True
```

## Приоритет

🟡 **Средний** — улучшает UX, но не критично для базовой функциональности

## Тестирование

### Unit-тесты

**Файл**: `tests/unit/handlers/test_commands.py`

```python
import pytest
from aiogram.types import CallbackQuery
from unittest.mock import Mock, patch
from handlers.commands import task_done_handler, task_delete_handler
from bot.db.file_manager import FileManager


class TestTaskDoneHandler:
    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Проверка выполнения задачи"""
        callback = Mock()
        callback.data = "task_done:task_001"
        callback.from_user.id = 123456
        
        with patch.object(FileManager, 'read_tasks') as mock_read, \
             patch.object(FileManager, 'update_task_status') as mock_update:
            
            mock_read.return_value = [
                Task(id="task_001", title="Test", status="pending", tags=[], content="")
            ]
            mock_update.return_value = True
            
            await task_done_handler(callback)
            
            assert mock_update.called
            assert callback.answer.called
    
    @pytest.mark.asyncio
    async def test_cancel_completion(self):
        """Проверка отмены выполнения задачи"""
        callback = Mock()
        callback.data = "task_done:task_001"
        callback.from_user.id = 123456
        
        with patch.object(FileManager, 'read_tasks') as mock_read, \
             patch.object(FileManager, 'update_task_status') as mock_update:
            
            mock_read.return_value = [
                Task(id="task_001", title="Test", status="completed", tags=[], content="")
            ]
            mock_update.return_value = True
            
            await task_done_handler(callback)
            
            assert mock_update.called


class TestTaskDeleteHandler:
    @pytest.mark.asyncio
    async def test_delete_task(self):
        """Проверка удаления задачи"""
        callback = Mock()
        callback.data = "task_delete:task_001"
        callback.from_user.id = 123456
        
        with patch.object(FileManager, 'read_tasks') as mock_read:
            mock_read.return_value = [
                Task(id="task_001", title="Test", status="pending", tags=[], content="")
            ]
            
            await task_delete_handler(callback)
            
            assert callback.answer.called
```

### Интеграционные тесты

**Файл**: `tests/integration/test_task_management.py`

```python
import pytest
from pathlib import Path
from bot.db.file_manager import FileManager
from bot.db.models import Task
from datetime import datetime


class TestTaskInlineActions:
    @pytest.fixture
    def file_manager(self, tmp_path):
        """Создать тестовый FileManager"""
        return FileManager(data_dir=str(tmp_path))
    
    @pytest.fixture
    def user_id(self):
        return 999999
    
    def test_complete_task(self, file_manager, user_id):
        """Тест выполнения задачи через FileManager"""
        # Создать задачу
        task = Task(
            id="task_001",
            title="Test Task",
            tags=["test"],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=["msg_001"],
            content="Test content"
        )
        file_manager.append_task(user_id, task)
        
        # Выполнить задачу
        success = file_manager.update_task_status(user_id, "task_001", "completed")
        assert success is True
        
        # Проверить статус
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].status == "completed"
    
    def test_delete_task(self, file_manager, user_id):
        """Тест удаления задачи"""
        # Создать задачу
        task = Task(
            id="task_002",
            title="To Delete",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        # Удалить задачу
        success = file_manager.delete_task(user_id, "task_002")
        assert success is True
        
        # Проверить удаление
        tasks = file_manager.read_tasks(user_id)
        assert len(tasks) == 0
    
    def test_toggle_task_status(self, file_manager, user_id):
        """Тест переключения статуса задачи"""
        task = Task(
            id="task_003",
            title="Toggle Test",
            tags=[],
            status="pending",
            created_at=datetime.now(),
            source_message_ids=[],
            content=""
        )
        file_manager.append_task(user_id, task)
        
        # Pending → Completed
        file_manager.update_task_status(user_id, "task_003", "completed")
        tasks = file_manager.read_tasks(user_id)
        assert tasks[0].status == "completed"
        
        # Completed → Pending
        file_manager.update_task_status(user_id, "task_003", "pending")
        tasks = file_manager.read_tasks(user_id)
        assert tasks[0].status == "pending"
=======
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
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
```

## Технические детали
- Task ID имеют формат `task_XXX` (например, `task_001`)
- Пользователь вводит только номер (например, `/done_123`)
- Нужно преобразовывать номер в формат `task_XXX` с добавлением ведущего нуля
- Для pending задач показывать обе команды: `/done_XXX` и `/del_XXX`
- Для completed задач показывать только `/del_XXX`

<<<<<<< HEAD
### Структура callback_data

Использовать формат `{action}:{id}` для парсинга:
- `task_done:task_001` — выполнить/отменить задачу
- `task_delete:task_001` — удалить задачу
- `task_delete_confirm:task_001` — подтвердить удаление
- `task_delete_cancel` — отмена удаления

### Обработка ошибок

1. **Задача не найдена** — показать alert с сообщением
2. **Ошибка обновления** — показать alert с ошибкой
3. **Некорректный callback_data** — игнорировать

### UX-улучшения

1. **Подтверждение удаления** — двухэтапное (выбор → подтверждение)
2. **Обновление сообщения** — редактировать вместо создания нового
3. **Feedback** — показывать `callback.answer()` для обратной связи
4. **Иконки статусов** — ✅ для выполненных, ⏳ для активных

## Обновление документации

### README.md

Добавить раздел о управлении задачами:

```markdown
## Управление задачами

### Просмотр задач
```
/tasks - список всех задач с кнопками управления
```

### Быстрые действия
- **✅ Выполнено** — переключить статус задачи
- **🗑 Удалить** — удалить задачу (с подтверждением)

### Пример
```
📋 Задачи:

⏳ Позвонить клиенту [работа]
   [✅ Выполнено] [🗑 Удалить]
```

### Команды
- `/tasks` — список задач
- `/task done <id>` — выполнить задачу (старый способ)
- `/task delete <id>` — удалить задачу (старый способ)
```

### handlers/commands.py

Добавить docstring для новых обработчиков:

```python
@router.callback_query(F.data.startswith("task_done:"))
async def task_done_handler(callback: CallbackQuery):
    """
    Обработка нажатия кнопки выполнения задачи.
    
    Callback data: task_done:{task_id}
    Переключает статус задачи между pending и completed.
    Обновляет сообщение с задачей.
    """
```

## Критерии приемки

- [x] Команда `/tasks` показывает задачи с inline-кнопками
- [x] Кнопка "✅ Выполнено" переключает статус задачи
- [x] Кнопка "🗑 Удалить" запрашивает подтверждение
- [x] Подтверждение удаления удаляет задачу и обновляет список
- [x] Отмена удаления возвращает к списку задач
- [x] Обработка ошибок (задача не найдена)
- [x] Обратная связь через `callback.answer()`
- [x] Обновление сообщения после действия
- [x] Unit-тесты для всех обработчиков
- [x] Интеграционные тесты для FileManager
- [x] Документация обновлена

## Изменения в файлах

**Новые файлы:**
- `tests/integration/test_task_management.py`

**Модифицированные файлы:**
- `handlers/commands.py` — добавить inline-кнопки и callback handlers
- `bot/db/file_manager.py` — добавить `delete_task()`
- `README.md` — обновить документацию

## Примечания

1. **Backward compatibility** — старые команды `/task done <id>` остаются рабочими
2. **Пагинация** — в будущем добавить для больших списков (>5 задач)
3. **Массовые действия** — в будущем добавить "Выполнить все" / "Удалить все"
4. **Архивация** — вместо удаления можно переносить в архив

## План реализации

1. Добавить метод `delete_task()` в `FileManager`
2. Модифицировать `tasks_handler()` для inline-кнопок
3. Добавить обработчики callback queries
4. Написать unit-тесты
5. Написать интеграционные тесты
6. Протестировать вручную
7. Обновить документацию
8. Закоммитить и запушить

---

**Создан**: 2026-03-08
**Автор**: Agent
**Версия**: 1.0
=======
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
>>>>>>> a154931 (feat: fix failing tests and complete TICKET-015)
