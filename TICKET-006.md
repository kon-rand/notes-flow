# TICKET-006: Саммаризатор

## Описание задачи
Реализовать основной процесс саммаризации: чтение сообщений, группировка, анализ AI, создание задач/заметок, очистка инбокса.

## Компоненты для реализации
- `handlers/summarizer.py` - auto_summarize для запуска саммаризации

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] auto_summarize(user_id) читает все сообщения из инбокса
- [ ] Группировка сообщений через ContextAnalyzer.group_messages
- [ ] Для каждой группы вызывается OllamaClient.summarize_group
- [ ] Создание задач/заметок через FileManager
- [ ] Очистка инбокса после обработки
- [ ] Отправка отчёта о результатах в чат Telegram
- [ ] Обработка ошибок при саммаризации

## Технические детали

### handlers/summarizer.py
```python
import asyncio
from typing import List, Dict, Any
from datetime import datetime

async def auto_summarize(user_id: int):
    """Автоматическая саммаризация по истечению задержки"""
    try:
        # 1. Чтение сообщений
        messages = FileManager.read_messages(user_id)
        
        if not messages:
            await send_message(user_id, "♻️ Инбокс уже пуст")
            return
        
        # 2. Группировка сообщений
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        # 3. Анализ каждой группы
        tasks_created = 0
        notes_created = 0
        skipped = 0
        report = []
        
        client = OllamaClient()
        
        for i, group in enumerate(groups, 1):
            result = await client.summarize_group(group)
            
            if result["action"] == "create_task":
                task = Task(
                    id=f"task_{i:03d}",
                    title=result["title"],
                    tags=result.get("tags", []),
                    content=result["content"],
                    source_message_ids=[m.id for m in group],
                    created_at=datetime.now()
                )
                FileManager.append_task(user_id, task)
                tasks_created += 1
                report.append(f"✅ Создана задача: {result['title']}")
            
            elif result["action"] == "create_note":
                note = Note(
                    id=f"note_{i:03d}",
                    title=result["title"],
                    tags=result.get("tags", []),
                    content=result["content"],
                    source_message_ids=[m.id for m in group],
                    created_at=datetime.now()
                )
                FileManager.append_note(user_id, note)
                notes_created += 1
                report.append(f"📝 Создана заметка: {result['title']}")
            
            else:
                skipped += 1
                report.append(f"⏭ Пропущено: {group[0].content[:50]}...")
        
        # 4. Очистка инбокса
        FileManager.clear_messages(user_id)
        
        # 5. Отправка отчёта
        report_text = f"""
♻️ Саммаризация завершена:

✅ Задачи создано: {tasks_created}
📝 Заметок создано: {notes_created}
⏭ Пропущено: {skipped}

{chr(10).join(report)}
"""
        await send_message(user_id, report_text.strip())
        
    except Exception as e:
        # Логирование ошибки
        await send_message(user_id, f"❌ Ошибка при саммаризации: {str(e)}")
```

### handlers/summarizer.py - команда /summarize
```python
@dp.message_handler(commands=["summarize"])
async def manual_summarize(message: Message):
    """Ручной запуск саммаризации"""
    user_id = message.from_user.id
    
    # Сбросить таймер
    SummarizeTimer.reset(user_id)
    
    # Запустить саммаризацию
    await auto_summarize(user_id)
```

## Требования к тестированию
- [ ] Unit-тесты для auto_summarize: обработка пустого инбокса
- [ ] Unit-тесты для auto_summarize: группировка сообщений через ContextAnalyzer
- [ ] Unit-тесты для auto_summarize: создание задач через OllamaClient
- [ ] Unit-тесты для auto_summarize: создание заметок через OllamaClient
- [ ] Unit-тесты для auto_summarize: пропуск групп через OllamaClient
- [ ] Unit-тесты для auto_summarize: очистка инбокса после обработки
- [ ] Unit-тесты для auto_summarize: отправка отчёта о результатах
- [ ] Unit-тесты для auto_summarize: обработка ошибок и отправка сообщения об ошибке
- [ ] Integration-тесты: полный цикл auto_summarize с разными сценариями
- [ ] Integration-тесты для команды /summarize: ручной запуск, сброс таймера
- [ ] Integration-тесты для команды /inbox: просмотр инбокса, пустой инбокс
- [ ] Edge cases: несколько групп сообщений, все группы пропущены, только задачи или только заметки

### handlers/commands.py - команда /inbox
```python
@dp.message_handler(commands=["inbox"])
async def inbox_handler(message: Message):
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
```