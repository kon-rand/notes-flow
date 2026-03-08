# TICKET-015: Инбокс не очищается при таймауте LLM запроса

## Описание

Когда запрос к LLM падает по таймауту (или другой ошибке), сообщения из инбокса всё равно очищаются. Это приводит к потере данных пользователя.

## Проблема

В `handlers/summarizer.py` код очистки инбокса выполняется **всегда**, даже если:
- LLM запрос таймаутнул
- Произошла ошибка API
- Все сообщения были пропущены (action=skip)

### Текущее поведение

```
2026-03-08 19:34:13,027 - utils.ollama_client - ERROR - ❌ TimeoutException
2026-03-08 19:34:13,028 - handlers.summarizer - INFO - → Результат: action=skip
2026-03-08 19:34:13,028 - handlers.summarizer - INFO - 💾 Сохранение backup
2026-03-08 19:34:13,028 - handlers.summarizer - INFO - 🗑️ Очистка инбокса выполнена ← ПРОБЛЕМА!
```

## Ожидаемое поведение

1. **Если запрос упал с ошибкой** (таймаут, API error) → инбокс НЕ очищается
2. **Backup сохраняется** при любой ошибке
3. **Ошибка выводится в чат** с сообщением, что сообщения сохранены
4. **Инбокс очищается только если** созданы хотя бы одна задача или заметка

## Требования

### Изменения в `handlers/summarizer.py`

1. Перенести очистку инбокса внутрь условия `if tasks_created > 0 or notes_created > 0`
2. Добавить логирование когда инбокс не очищается
3. Добавить отправку сообщения об ошибке в чат при таймауте

### Пример кода

```python
# Вместо:
logger.info(f"💾 Сохранение backup перед очисткой инбокса")
backup_path = file_manager.save_backup(user_id)
file_manager.clear_messages(user_id)
logger.info(f"🗑️ Очистка инбокса выполнена")

# Написать:
if tasks_created > 0 or notes_created > 0:
    logger.info(f"💾 Сохранение backup перед очисткой инбокса")
    backup_path = file_manager.save_backup(user_id)
    file_manager.clear_messages(user_id)
    logger.info(f"🗑️ Очистка инбокса выполнена")
else:
    logger.warning(f"⚠️ Ничего не создано, инбокс не очищается")
```

### Сообщение об ошибке в чат

```python
if bot and (tasks_created == 0 and notes_created == 0):
    try:
        await bot.send_message(
            user_id,
            "❌ Ошибка при саммаризации\n\n📦 Ваши сообщения сохранены в backup и не удалены"
        )
    except Exception:
        pass
```

## Тесты

Добавить тест в `tests/integration/test_summarizer_integration.py`:

```python
@pytest.mark.asyncio
async def test_inbox_not_cleared_on_timeout(clean_data_dir):
    """Таймаут LLM → инбокс НЕ очищается"""
    user_id = 123456789
    fm = FileManager()
    
    message = InboxMessage(
        id="msg_001",
        timestamp=datetime.now(),
        from_user=user_id,
        sender_id=user_id,
        sender_name="Test",
        content="Нужно сделать задачу",
        chat_id=-1001234567890
    )
    fm.append_message(user_id, message)
    
    # Мокируем таймаут
    with patch.object(OpenAIClient, 'summarize_group', new_callable=AsyncMock) as mock_summarize:
        mock_summarize.return_value = {"action": "skip", "reason": "Timeout"}
        
        mock_bot = AsyncMock()
        await auto_summarize(user_id, bot=mock_bot)
    
    # Инбокс НЕ должен быть очищен
    messages = fm.read_messages(user_id)
    assert len(messages) == 1, "Инбокс должен оставаться не пустым при таймауте"
    
    # Backup должен быть создан
    assert os.path.exists(f"data/{user_id}/inbox_backup_*.md")
```

## Технические детали

- Таймаут по умолчанию: 120 секунд (достаточно для малых моделей)
- Для больших моделей (Qwen3.5-35B) увеличить до 300 секунд
- Логировать причину ошибки для отладки

## Приоритет

🔴 **Высокий** - критичная проблема с потерей данных

## Критерии приёмки

- [ ] Таймаут LLM → инбокс не очищается
- [ ] Backup создаётся при любой ошибке
- [ ] Пользователь получает сообщение об ошибке в чат
- [ ] Инбокс очищается только при успешном создании задач/заметок
- [ ] Добавлены тесты для проверки поведения