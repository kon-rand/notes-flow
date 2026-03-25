# TICKET-023: Исправить команду /settings для Konstantin Zakhmatov

## Описание

Команда `/settings` для пользователя zahmatovk-claw не работает корректно. Пользователь отправляет `/settings 2` и получает сообщение о текущей задержке, но настройки не применяются.

**Проблема**: Пользователь не может изменить задержку саммаризации через команду `/settings delay <минуты>`.

## Компоненты
- [x] Найти и понять текущую реализацию команды `/settings`
- [x] Найти и понять, как хранятся настройки пользователей
- [x] Определить причину, почему параметр задержки не применяется
- [ ] Создать модуль персональных настроек пользователей
- [ ] Изменить парсинг команды `/settings` для поддержки формата `/settings <минуты>`
- [ ] Обновить SummarizeTimer для использования персональных настроек
- [ ] Добавить тесты для команды `/settings`
- [ ] Обновить документацию (README.md)

## Приоритет
🟡 средний

## Статус
🚧 in_progress - требует реализации

---

## Анализ проблемы

### 1. Текущая реализация команды `/settings` (handlers/commands.py:91-125)

```python
@router.message(Command("settings"))
async def settings_handler(message: Message):
    parts = message.text.split() if message.text else []
    
    # Проблема здесь! Требуется `/settings delay <минуты>`
    if len(parts) > 2 and parts[1] == "delay":
        # Обработка настройки задержки
    else:
        # Просто показывает текущую задержку
```

**Проблема**: Условие `len(parts) > 2` требует как минимум 3 элемента:
- `/settings delay 2` -> `["/settings", "delay", "2"]` -> len = 3 ✅
- `/settings 2` -> `["/settings", "2"]` -> len = 2 ❌ (не срабатывает!)

### 2. Глобальные настройки вместо пользовательских

`settings.DEFAULT_SUMMARIZE_DELAY` - это глобальная настройка:
- Нет персистентного хранилища для настроек конкретного пользователя
- Изменение влияет на ВСЕХ пользователей, а не только на того, кто изменил

### 3. Как SummarizeTimer получает задержку

В `bot/timers/manager.py:9-17`:
```python
async def schedule_summarization(self, user_id: int, delay_seconds: int) -> None:
    task = asyncio.create_task(self._wait_and_summarize(user_id, delay_seconds))
```

При создании таймера значение delay_seconds передаётся как параметр и "зашивается" в момент создания.

---

## Реализация

### Шаг 1: Создать модуль персональных настроек

**Файл**: `bot/config/user_settings.py` (новый файл)

```python
"""Персональные настройки пользователей"""
import json
import os
from typing import Dict

SETTINGS_FILE = "data/user_settings.json"

class UserSettings:
    def __init__(self):
        self._settings: Dict[int, int] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    self._settings = {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self._settings = {}
    
    def _save(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self._settings, f)
    
    def get_delay(self, user_id: int, default: int = None) -> int:
        return self._settings.get(user_id, default)
    
    def set_delay(self, user_id: int, delay_seconds: int):
        self._settings[user_id] = delay_seconds
        self._save()
    
    def get_user_delay(self, user_id: int) -> int:
        from bot.config import settings
        return self._settings.get(user_id, settings.DEFAULT_SUMMARIZE_DELAY)


user_settings = UserSettings()
```

### Шаг 2: Изменить парсинг команды `/settings`

**Файл**: `handlers/commands.py:91-130`

Изменить функцию `settings_handler`:

```python
@router.message(Command("settings"))
async def settings_handler(message: Message):
    """Настройка задержки саммаризации"""
    if message.from_user is None:
        return
    parts = message.text.split() if message.text else []
    
    # Новый формат: /settings <минуты> (без слова "delay")
    if len(parts) == 2 and parts[1].isdigit():
        delay_minutes = int(parts[1])
    # Старый формат: /settings delay <минуты>
    elif len(parts) > 2 and parts[1] == "delay":
        try:
            delay_minutes = int(parts[2])
        except ValueError:
            await message.answer("Некорректное значение задержки. Используйте: /settings <минуты>")
            return
    else:
        # Показать текущую задержку
        from bot.config.user_settings import user_settings
        current_delay = user_settings.get_user_delay(message.from_user.id)
        current_delay_minutes = current_delay // 60
        await message.answer(f"Текущая задержка: {current_delay_minutes} минут\nИспользуйте: /settings <минуты>")
        return
    
    delay_seconds = delay_minutes * 60
    
    if delay_minutes < 1:
        await message.answer("Задержка должна быть не менее 1 минуты")
        return
    
    # Сохранить персональную настройку
    from bot.config.user_settings import user_settings
    user_settings.set_delay(message.from_user.id, delay_seconds)
    
    # Сбросить и перезапустить таймер с новой задержкой
    from bot.timers.manager import summarizer_timer
    await summarizer_timer.reset(message.from_user.id)
    asyncio.create_task(summarizer_timer.schedule_summarization(message.from_user.id, delay_seconds))
    
    await message.answer(f"Задержка установлена на {delay_minutes} минут ({delay_seconds} секунд)")
```

### Шаг 3: Обновить SummarizeTimer для использования персональных настроек

**Файл**: `bot/timers/manager.py:9-17`

```python
async def schedule_summarization(self, user_id: int, delay_seconds: int = None) -> None:
    """Запланировать саммаризацию с задержкой"""
    # Если delay_seconds не передан - получить из персональных настроек
    if delay_seconds is None:
        from bot.config.user_settings import user_settings
        delay_seconds = user_settings.get_user_delay(user_id)
    
    if user_id in self.timers:
        old_task = self.timers[user_id]
        old_task.cancel()
        await asyncio.sleep(0.01)

    task = asyncio.create_task(self._wait_and_summarize(user_id, delay_seconds))
    self.timers[user_id] = task
```

---

## Тестирование

### Требования к тестам

Добавить в `tests/unit/handlers/test_commands.py`:

1. **Тест на короткий формат `/settings <минуты>`**:
```python
@pytest.mark.asyncio
async def test_settings_handler_short_form(mock_message):
    """Тест: /settings <минуты> - короткий формат"""
    mock_message.text = "/settings 10"
    
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer_instance:
        
        mock_user_settings.set_delay = MagicMock()
        mock_timer_instance.reset = AsyncMock()
        mock_timer_instance.schedule_summarization = AsyncMock()
        
        await settings_handler(mock_message)
        
        mock_user_settings.set_delay.assert_called_once_with(123456789, 600)
        mock_timer_instance.reset.assert_called_once_with(123456789)
        mock_timer_instance.schedule_summarization.assert_called_once_with(123456789, 600)
        assert "Задержка установлена на 10 минут" in mock_message.answer.call_args[0][0]
```

2. **Тест на возврат текущей задержки при `/settings` без параметров**:
```python
@pytest.mark.asyncio
async def test_settings_handler_show_current_delay(mock_message):
    """Тест: /settings без параметров показывает текущую задержку"""
    with patch('handlers.commands.user_settings') as mock_user_settings:
        mock_user_settings.get_user_delay.return_value = 300  # 5 минут
        
        await settings_handler(mock_message)
        
        assert "Текущая задержка: 5 минут" in mock_message.answer.call_args[0][0]
```

3. **Тест на применение новой задержки**:
```python
@pytest.mark.asyncio
async def test_settings_handler_applies_new_delay(mock_message):
    """Тест: /settings 2 применяет новую задержку"""
    mock_message.text = "/settings 2"
    
    with patch('handlers.commands.user_settings') as mock_user_settings, \
         patch('handlers.commands.summarizer_timer') as mock_timer:
        
        mock_user_settings.set_delay = MagicMock()
        mock_timer.reset = AsyncMock()
        mock_timer.schedule_summarization = AsyncMock()
        
        await settings_handler(mock_message)
        
        mock_user_settings.set_delay.assert_called_once_with(123456789, 120)  # 2 мин
        mock_timer.schedule_summarization.assert_called_once_with(123456789, 120)
```

---

## Обновление документации

### README.md

Обновить раздел "Команды бота":

```markdown
| Команда | Описание |
|---------|----------|
| /start | Приветствие и статистика |
| /summarize | Ручной запуск саммаризации |
| /inbox | Просмотр текущего инбокса |
| /tasks | Список задач |
| /notes | Список заметок |
| /settings | Показать текущую задержку |
| /settings <минуты> | Установить задержку в минутах |
| /settings delay <минуты> | Установить задержку (альтернативный формат) |
| /clear inbox | Очистка инбокса вручную |
```

Добавить пример использования в раздел "Примеры использования":

```markdown
**Настройка задержки саммаризации:**
```
Вы: /settings 2
Бот: Задержка установлена на 2 минуты (120 секунд)

Вы: /settings
Бот: Текущая задержка: 5 минут
     Используйте: /settings <минуты>
```
```
