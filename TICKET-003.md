# TICKET-003: Таймеры

## Описание задачи
Реализовать систему управления задержками перед саммаризацией: планирование, сброс при новых сообщениях, асинхронный таймер.

## Компоненты для реализации
- `bot/timers/manager.py` - SummarizeTimer для управления задержками
- `handlers/commands.py` - команды управления таймерами

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] SummarizeTimer.schedule_summarization(user_id, delay_seconds) планирует саммаризацию
- [ ] SummarizeTimer.reset(user_id) отменяет предыдущий таймер при новом сообщении
- [ ] Асинхронный метод _wait_and_summarize работает корректно
- [ ] Таймер сбрасывается при получении новых сообщений
- [ ] Команда /settings позволяет настроить задержку
- [ ] Задержка по умолчанию 300 секунд (5 минут)

## Технические детали

### bot/timers/manager.py
```python
import asyncio
from typing import Dict
from datetime import datetime

class SummarizeTimer:
    def __init__(self):
        self.timers: Dict[int, asyncio.Task] = {}
    
    async def schedule_summarization(self, user_id: int, delay_seconds: int):
        """Запланировать саммаризацию с задержкой"""
        # Отменить предыдущий таймер если есть
        if user_id in self.timers:
            self.timers[user_id].cancel()
        
        # Создать новый таймер
        task = asyncio.create_task(self._wait_and_summarize(user_id, delay_seconds))
        self.timers[user_id] = task
    
    async def reset(self, user_id: int):
        """Сбросить таймер при новом сообщении"""
        if user_id in self.timers:
            self.timers[user_id].cancel()
            del self.timers[user_id]
    
    async def _wait_and_summarize(self, user_id: int, delay: int):
        """Асинхронный таймер с задержкой"""
        await asyncio.sleep(delay)
        
        # Запустить саммаризацию
        from handlers.summarizer import auto_summarize
        await auto_summarize(user_id)
```

### handlers/commands.py - команда /settings
```python
@dp.message_handler(commands=["settings"])
async def settings_handler(message: Message):
    """Настройка задержки саммаризации"""
    if len(message.text.split()) > 1:
        delay_minutes = int(message.text.split()[1])
        delay_seconds = delay_minutes * 60
        
        # Сохранить настройку
        # Обновить таймер
        SummarizeTimer.schedule_summarization(message.from_user.id, delay_seconds)
        
        await message.answer(f"Задержка установлена на {delay_minutes} минут")
    else:
        await message.answer("Используйте: /settings delay <минуты>")
```

### Интеграция с обработкой сообщений
```python
# handlers/messages.py
@dp.message_handler(content_types=["text"])
async def message_handler(message: Message):
    user_id = message.from_user.id
    
    # Сбросить предыдущий таймер
    SummarizeTimer.reset(user_id)
    
    # Сохранить сообщение
    FileManager.append_message(user_id, inbox_message)
    
    # Запланировать саммаризацию
    delay = Settings.DEFAULT_SUMMARIZE_DELAY
    await SummarizeTimer.schedule_summarization(user_id, delay)
```

## Требования к тестированию
- [ ] Unit-тесты для SummarizeTimer.schedule_summarization: создание asyncio.Task, добавление в словарь
- [ ] Unit-тесты для SummarizeTimer.reset: отмена task, удаление из словаря
- [ ] Unit-тесты для _wait_and_summarize: корректная задержка, вызов auto_summarize
- [ ] Integration-тесты: обработка новых сообщений → reset таймера → schedule новый
- [ ] Тестирование отмены предыдущих таймеров при schedule нового
- [ ] Проверка работы с несколькими user_id: изоляция таймеров
- [ ] Integration-тесты команды /settings: парсинг аргументов, сохранение задержки, обновление таймера
- [ ] Edge cases: отмена task до завершения, повторный reset одного таймера