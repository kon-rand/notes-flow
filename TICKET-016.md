# TICKET-016: Архивация выполненных задач

## Описание

Реализовать систему архивации выполненных задач по дням с командами для просмотра и принудительной архивации.

## Задачи

### 1. Модификация модели Task

Добавить поле для отслеживания даты архивации:

```python
class Task(BaseModel):
    id: str
    title: str
    tags: List[str]
    status: str = "pending"  # pending, completed
    created_at: datetime
    completed_at: datetime | None = None  # Дата выполнения
    archived_at: datetime | None = None   # Дата архивации
    source_message_ids: List[str]
    content: str
```

### 2. FileManager - методы для архивации

Добавить методы в `bot/db/file_manager.py`:

```python
def archive_completed_tasks(self, user_id: int, date: datetime) -> List[Task]:
    """Перенести все выполненные задачи в архив за указанную дату"""
    # 1. Найти все completed задачи у пользователя
    # 2. Найти файл архива для даты: data/{user_id}/archive/{date}.md
    # 3. Добавить задачи в файл архива
    # 4. Удалить задачи из tasks.md
    # 5. Обновить archived_at у задач
    # 6. Вернуть список перенесённых задач
```

```python
def get_archive_dates(self, user_id: int) -> List[str]:
    """Получить список дат, для которых есть файлы архива"""
    # Вернуть список в формате "YYYY-MM-DD"
```

```python
def get_tasks_by_archive_date(self, user_id: int, date: str) -> List[Task]:
    """Получить все задачи из архива за указанную дату"""
    # Вернуть задачи из data/{user_id}/archive/{date}.md
```

### 3. handlers/commands.py - новые команды

Добавить команды:

**`/completed`** - показать список дат с архивом:
```python
@dp.message(Command("complete"))
async def cmd_complete(message: Message):
    """Показать список дат с завершёнными задачами в архиве"""
    dates = file_manager.get_archive_dates(user_id)
    if not dates:
        await message.answer("Нет завершённых задач в архиве")
        return
    
    text = "📁 Завершённые задачи по датам:\n\n"
    for date in sorted(dates, reverse=True):
        tasks = file_manager.get_tasks_by_archive_date(user_id, date)
        count = len(tasks)
        text += f"📅 {date} — {count} задач\n"
    
    await message.answer(text)
```

**`/completed_YYYY_MM_DD`** - показать задачи за конкретную дату:
```python
@dp.message(Command("complete_"))
async def cmd_complete_date(message: Message):
    """Показать все завершённые задачи за указанную дату (формат YYYY_MM_DD)"""
    date_str = message.text.replace("/completed_", "")
    
    try:
        # Проверить формат даты (YYYY_MM_DD)
        datetime.strptime(date_str, "%Y_%m_%d")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте YYYY_MM_DD")
        return
    
    tasks = file_manager.get_tasks_by_archive_date(user_id, date_str)
    if not tasks:
        await message.answer(f"Нет завершённых задач за {date_str}")
        return
    
    text = f"📁 Завершённые задачи за {date_str}:\n\n"
    for task in tasks:
        text += f"✅ {task.title}\n"
        if task.tags:
            text += f"   🏷️ {', '.join(task.tags)}\n"
        text += f"   📝 {task.content}\n\n"
    
    await message.answer(text)
```

**`/archive`** - принудительная архивация:
```python
@dp.message(Command("archive"))
async def cmd_archive(message: Message):
    """Перенести все выполненные задачи из /tasks в архив за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    archived = file_manager.archive_completed_tasks(user_id, today)
    if not archived:
        await message.answer("Нет выполненных задач для архивации")
        return
    
    text = f"✅ Заархивировано {len(archived)} задач за {today}:\n\n"
    for task in archived:
        text += f"📝 {task.title}\n"
    
    await message.answer(text)
```

### 4. Автоматическая архивация (опционально)

Добавить фоновую задачу для ночной архивации:

```python
# bot/timers/manager.py
class TaskArchiver:
    """Фоновый архиватор выполненных задач"""
    
    async def start_nightly_archive(self, user_id: int):
        """Запустить ночную архивацию (например, в 02:00)"""
        while True:
            now = datetime.now()
            next_archive = datetime(now.year, now.month, now.day) + timedelta(days=1)
            next_archive = next_archive.replace(hour=2, minute=0, second=0, microsecond=0)
            
            delay = (next_archive - now).total_seconds()
            await asyncio.sleep(delay)
            
            file_manager.archive_completed_tasks(user_id, now.strftime("%Y-%m-%d"))
```

### 5. Структура файлов

```
data/
└── {user_id}/
    ├── inbox.md
    ├── tasks.md
    ├── notes.md
    └── archive/
        ├── 2026-02-21.md
        ├── 2026-02-22.md
        └── 2026-03-10.md
```

Пример файла архива:
```yaml
---
type: archived_tasks
date: 2026-03-10
---

## task_001
title: Подготовить отчёт
tags: [работа]
status: completed
created_at: 2026-03-09T10:00:00
completed_at: 2026-03-10T09:00:00
archived_at: 2026-03-10T02:00:00
source_message_ids: [msg_001, msg_002]
content: Отчёт подготовлен и отправлен
```

## Тестирование

### Unit-тесты

```python
# tests/unit/db/test_file_manager_archive.py

def test_archive_completed_tasks():
    """Проверить архивацию выполненных задач"""
    fm = FileManager("test_user")
    
    # Создать выполненные задачи
    task1 = Task(
        id="task_001",
        title="Тестовая задача 1",
        status="completed",
        completed_at=datetime(2026-03-10, 9, 0)
    )
    task2 = Task(
        id="task_002",
        title="Тестовая задача 2",
        status="completed",
        completed_at=datetime(2026-03-10, 10, 0)
    )
    
    fm.append_task("test_user", task1)
    fm.append_task("test_user", task2)
    
    # Архивация
    archived = fm.archive_completed_tasks("test_user", datetime(2026-03-10))
    
    assert len(archived) == 2
    assert all(t.archived_at is not None for t in archived)
    
    # Задачи должны быть удалены из tasks.md
    tasks = fm.read_tasks("test_user")
    assert len(tasks) == 0
    
    # Задачи должны быть в архиве
    archive_tasks = fm.get_tasks_by_archive_date("test_user", "2026-03-10")
    assert len(archive_tasks) == 2

def test_get_archive_dates():
    """Проверить получение списка дат архива"""
    fm = FileManager("test_user")
    
    # Создать архивные файлы
    os.makedirs(f"data/test_user/archive", exist_ok=True)
    Path(f"data/test_user/archive/2026-03-10.md").write_text(...)
    Path(f"data/test_user/archive/2026-03-11.md").write_text(...)
    
    dates = fm.get_archive_dates("test_user")
    
    assert "2026-03-10" in dates
    assert "2026-03-11" in dates
```

### Интеграционные тесты

```python
# tests/integration/test_commands_archive.py

async def test_complete_command():
    """Проверить команду /completed"""
    # Создать тестового пользователя с архивом
    # Отправить /completed
    # Проверить ответ с перечнем дат
    
async def test_complete_date_command():
    """Проверить команду /completed_2026_03_10"""
    # Создать архив за 2026-03-10
    # Отправить /completed_2026_03_10
    # Проверить вывод задач
```

## Требования к документации

Обновить:
1. **PLAN.md** - добавить TICKET-016 в список
2. **README.md** - добавить новые команды в таблицу
3. **bot/db/file_manager.py** - добавить docstring для новых методов
4. **handlers/commands.py** - добавить docstring для новых команд

## Технические детали

### Обработка форматов дат

- Внутреннее хранение: `datetime` объекты
- Файлы архива: `YYYY-MM-DD.md`
- Команда `/completed_YYYY_MM_DD`: принимает `_` вместо `-`
- Вывод команд: `YYYY-MM-DD`

### Обработка ошибок

```python
def archive_completed_tasks(self, user_id: int, date: datetime) -> List[Task]:
    """Архивация с обработкой ошибок"""
    try:
        # Проверка существования пользователя
        if not self._user_exists(user_id):
            return []
        
        # Чтение всех задач
        tasks = self.read_tasks(user_id)
        
        # Фильтрация выполненных
        completed = [t for t in tasks if t.status == "completed" and t.completed_at.date() == date.date()]
        
        if not completed:
            return []
        
        # Создание папки архива
        archive_dir = Path(f"data/{user_id}/archive")
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Запись в файл архива
        archive_file = archive_dir / f"{date.strftime('%Y-%m-%d')}.md"
        self._append_to_archive(archive_file, completed)
        
        # Удаление из tasks.md
        self._remove_tasks(user_id, completed)
        
        return completed
        
    except Exception as e:
        logger.error(f"Ошибка архивации для {user_id}: {e}")
        return []
```

## Критерии готовности

- [x] Добавлено поле `completed_at` в модель Task
- [x] Реализованы методы FileManager для архивации
- [x] Реализованы команды `/completed`, `/completed_YYYY_MM_DD`, `/archive`
- [x] Файлы архива хранятся по дням (`YYYY-MM-DD.md`)
- [x] Unit-тесты для методов FileManager
- [x] Интеграционные тесты для команд
- [x] Документация обновлена

## Приоритет

🟡 средний

## Связанные тикеты

- TICKET-015: Управление задачами (выполнение и удаление)