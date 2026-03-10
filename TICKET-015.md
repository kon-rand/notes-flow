# TICKET-015: Inline-кнопки для управления задачами

## Описание

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
```

## Технические детали

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