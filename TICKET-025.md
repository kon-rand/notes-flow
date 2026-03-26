# TICKET-025: Исправить логику запуска автосаммаризации

## Описание

**Проблема:**
1. Ручная саммаризация по команде `/summarize` не отменяет запланированную автосаммаризацию
2. Автосаммаризация запускается на каждое сообщение вместо того, чтобы запускаться один раз на батч сообщений

**Ожидаемое поведение:**
1. Ручная саммаризация должна отменять все запланированные таймеры автосаммаризации для пользователя
2. Автосаммаризация должна запускаться один раз после получения батча сообщений, а не на каждое сообщение отдельно

## Компоненты

- [ ] `handlers/summarizer.py` - команда `/summarize`
- [ ] `bot/timers/manager.py` - `SummarizeTimer`
- [ ] `handlers/messages.py` - обработка сообщений

## Приоритет

🔴 высокий

## Статус

⏳ pending - требует проработки

## Технические детали

### Текущая реализация

В `handlers/messages.py`:
```python
async def message_handler(message: Message) -> None:
    # ... сохранение сообщения ...
    
    # Запуск таймера на каждое сообщение
    await summarizer_timer.schedule_summarization(
        user_id=user_id,
        user_name=user_name,
        bot=message.bot
    )
```

В `bot/timers/manager.py`:
```python
async def schedule_summarization(self, user_id: int, ...) -> None:
    if user_id in self.timers:
        old_task = self.timers[user_id]
        old_task.cancel()
        await asyncio.sleep(0.01)
```

Проблема: Таймер сбрасывается на каждое новое сообщение, но ручная саммаризация не очищает таймеры.

### Требуемые изменения

#### 1. Добавить метод для ручного запуска саммаризации

В `bot/timers/manager.py`:
```python
async def trigger_immediate_summarization(self, user_id: int, bot: Bot, user_name: str) -> None:
    """Мгновенно запустить саммаризацию и сбросить все таймеры"""
    # Отправить уведомление
    try:
        await bot.send_message(
            user_id,
            f"🔄 Ручная саммаризация началась для пользователя {user_name}"
        )
    except Exception:
        pass
    
    # Сбросить все таймеры для пользователя
    if user_id in self.timers:
        self.timers[user_id].cancel()
        del self.timers[user_id]
        await asyncio.sleep(0.01)
    
    # Мгновенно запустить саммаризацию
    from handlers.summarizer import auto_summarize
    await auto_summarize(user_id, bot=bot)
```

#### 2. Обновить команду `/summarize`

В `handlers/summarizer.py`:
```python
@dp.message(Command("summarize"))
async def summarizer_handler(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # Запустить немедленную саммаризацию через таймер
    await summarizer_timer.trigger_immediate_summarization(
        user_id=user_id,
        bot=message.bot,
        user_name=user_name
    )
```

#### 3. Убедиться, что таймер сбрасывается на каждое сообщение

Проверить, что текущая логика в `schedule_summarization()` корректно отменяет предыдущий таймер.

## Требования к тестированию

### Unit тесты

`tests/unit/bot/timers/test_summarize_timer.py`:

```python
@pytest.mark.asyncio
async def test_trigger_immediate_summarization_cancels_pending_timer(timer, mock_bot):
    """Verify manual summarization cancels pending auto summarization"""
    # Schedule auto summarization
    await timer.schedule_summarization(
        user_id=123,
        delay_seconds=300,
        user_name="Test User",
        bot=mock_bot
    )
    
    # Wait for timer to be scheduled
    await asyncio.sleep(0.1)
    
    # Trigger immediate summarization
    await timer.trigger_immediate_summarization(
        user_id=123,
        bot=mock_bot,
        user_name="Test User"
    )
    
    # Verify pending timer was cancelled
    assert 123 not in timer.timers
    
    # Verify immediate summarization was triggered
    mock_bot.send_message.assert_called()

@pytest.mark.asyncio
async def test_trigger_immediate_summarization_sends_notification(timer, mock_bot):
    """Verify immediate summarization sends notification"""
    await timer.trigger_immediate_summarization(
        user_id=456,
        bot=mock_bot,
        user_name="Test User"
    )
    
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert "Ручная саммаризация началась" in call_args[0][1]
```

### Интеграционные тесты

`tests/integration/test_summarizer_integration.py`:

```python
@pytest.mark.asyncio
async def test_manual_summarization_cancels_auto_summarization():
    """Test that /summarize command cancels pending auto summarization"""
    # Send message to schedule auto summarization
    await send_message_to_bot("test message")
    await asyncio.sleep(0.1)
    
    # Send /summarize command
    await send_command_to_bot("/summarize")
    await asyncio.sleep(0.5)
    
    # Verify manual summarization was triggered
    # (check that bot sent notification)
```

## Примеры

### Сценарий 1: Ручная саммаризация отменяет автосаммаризацию

**Дано:**
- Пользователь отправил сообщение в 10:00
- Авто-саммаризация запланирована на 10:05 (задержка 5 минут)

**Когда:**
- В 10:02 пользователь отправляет команду `/summarize`

**Ожидаемо:**
- Авто-саммаризация на 10:05 отменяется
- Бот сразу отправляет уведомление: "🔄 Ручная саммаризация началась"
- Бот обрабатывает все сообщения в инбоксе
- Бот отправляет результат саммаризации

### Сценарий 2: Автосаммаризация один раз на батч

**Дано:**
- Пользователь отправляет 5 сообщений подряд в течение 3 минут

**Ожидаемо:**
- Первое сообщение: таймер запускается на 10:05
- Второе сообщение: таймер сбрасывается и перезапускается на 10:06
- Третье сообщение: таймер сбрасывается и перезапускается на 10:07
- Четвёртое сообщение: таймер сбрасывается и перезапускается на 10:08
- Пятое сообщение: таймер сбрасывается и перезапускается на 10:09
- В 10:09 запускается автосаммаризация ОДИН РАЗ со всеми 5 сообщениями

## Критерии готовности

- [ ] Ручная саммаризация отменяет все запланированные таймеры
- [ ] Ручная саммаризация отправляет уведомление пользователю
- [ ] Автосаммаризация сбрасывается на каждое новое сообщение
- [ ] Автосаммаризация запускается один раз на батч сообщений
- [ ] Все unit тесты проходят
- [ ] Все интеграционные тесты проходят
- [ ] README.md обновлён (если есть документация по командам)
