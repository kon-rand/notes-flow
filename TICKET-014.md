# TICKET-014: Исправление обработки ошибок в OpenAIClient

## Описание задачи

`OpenAClient.summarize_group()` перехватывает все ошибки (таймаут, сеть) и возвращает `{"action": "skip", ...}` вместо того чтобы выбросить исключение. Это приводит к тому, что:
- Инбокс не очищается (хорошо)
- Но пользователь НЕ получает сообщение об ошибке
- Ошибка остается незамеченной

## Текущая проблема

В `utils/ollama_client.py:67-79`:

```python
except httpx.TimeoutException as e:
    logger.error(f"❌ TimeoutException: {e}")
    return {"action": "skip", "reason": "Request timeout"}  # ❌ Возвращает skip вместо исключения
```

Это означает, что `summarizer.py` думает, что LLM успешно ответила с `action=skip`, и:
- Не очищает инбокс (потому что action=skip)
- Не отправляет сообщение об ошибке пользователю
- Ошибка просто логируется, но пользователь о ней не знает

## Требования

### 1. Разделить ошибки в `utils/ollama_client.py`

Создать кастомное исключение для критических ошибок:

```python
# utils/ollama_client.py
class LLMError(Exception):
    """Базовое исключение для ошибок LLM"""
    pass

class LLMTimeoutError(LLMError):
    """Таймаут запроса к LLM"""
    pass

class LLMNetworkError(LLMError):
    """Сетевая ошибка при обращении к LLM"""
    pass

class LLMResponseError(LLMError):
    """Ошибка ответа от LLM (неверный формат, HTTP ошибки)"""
    pass
```

### 2. Изменить обработку ошибок в `summarize_group()`

```python
async def summarize_group(self, messages: List[InboxMessage]) -> Dict[str, Any]:
    # ... код до try ...
    
    try:
        response = await self.client.post(...)
        # ... обработка ответа ...
        
    except httpx.TimeoutException as e:
        logger.error(f"❌ TimeoutException: {e}")
        raise LLMTimeoutError(f"Request timeout after {self.client.timeout}s")
    
    except httpx.ConnectError as e:
        logger.error(f"❌ ConnectError: {e}")
        raise LLMNetworkError("LLM API not available")
    
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTPStatusError: {e.response.status_code}")
        raise LLMResponseError(f"HTTP error: {e.response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
        raise LLMError(f"Unexpected error: {type(e).__name__}")
```

### 3. Обработать исключения в `handlers/summarizer.py`

```python
from utils.ollama_client import LLMTimeoutError, LLMNetworkError, LLMResponseError, LLMError

async def auto_summarize(user_id: int, bot: Optional[Bot] = None):
    # ... код до try ...
    
    try:
        for i, group in enumerate(groups, 1):
            result = await client.summarize_group(group)
            # ... обработка результата ...
    
    except LLMTimeoutError as e:
        logger.error(f"❌ Таймаут LLM: {str(e)}")
        if bot:
            await bot.send_message(user_id,
                "❌ Таймаут при обращении к LLM\n\n"
                "💡 Ваши сообщения сохранены и будут обработаны позже.\n"
                "🔄 Попробуйте /summarize снова через 5-10 минут."
            )
        return {"error": "timeout", "message": str(e)}
    
    except LLMNetworkError as e:
        logger.error(f"❌ Сетевая ошибка LLM: {str(e)}")
        if bot:
            await bot.send_message(user_id,
                "❌ Сетевая ошибка при обращении к LLM\n\n"
                "💡 Проверьте соединение и попробуйте снова."
            )
        return {"error": "network", "message": str(e)}
    
    except LLMResponseError as e:
        logger.error(f"❌ Ошибка ответа LLM: {str(e)}")
        if bot:
            await bot.send_message(user_id,
                f"❌ Ошибка ответа от LLM: {str(e)}\n\n"
                "💡 Ваши сообщения сохранены.\n"
                "🔄 Попробуйте /summarize снова."
            )
        return {"error": "response", "message": str(e)}
    
    except LLMError as e:
        logger.error(f"❌ Ошибка LLM: {str(e)}")
        if bot:
            await bot.send_message(user_id,
                f"❌ Ошибка: {str(e)}\n\n"
                "💡 Ваши сообщения сохранены.\n"
                "🔄 Попробуйте /summarize снова."
            )
        return {"error": "unknown", "message": str(e)}
```

### 4. Тестирование

Создать тесты:

1. **test_ollama_client_timeout_error** - Таймаут выбрасывает LLMTimeoutError
2. **test_ollama_client_network_error** - Сетевая ошибка выбрасывает LLMNetworkError
3. **test_ollama_client_http_error** - HTTP ошибка выбрасывает LLMResponseError
4. **test_summarizer_timeout_handling** - Summarizer корректно обрабатывает LLMTimeoutError
5. **test_summarizer_network_handling** - Summarizer корректно обрабатывает LLMNetworkError
6. **test_summarizer_error_inbox_preserved** - При LLM ошибке инбокс не очищается

## Технические детали

### Структура исключений

```
LLMError (базовое)
├── LLMTimeoutError
├── LLMNetworkError
├── LLMResponseError
└── LLM parsing error (можно добавить позже)
```

### Логирование

Все исключения должны логироваться с полным traceback:

```python
import traceback

except LLMTimeoutError as e:
    logger.error(f"❌ LLMTimeoutError: {str(e)}")
    logger.error(f"   Stack:\n{traceback.format_exc()}")
```

## Приоритет

🔴 **Высокий** - Критично для UX, пользователи не знают об ошибках

## Критерии приемки

- [ ] При таймауте выбрасывается `LLMTimeoutError`
- [ ] При сетевой ошибке выбрасывается `LLMNetworkError`
- [ ] При HTTP ошибке выбрасывается `LLMResponseError`
- [ ] Summarizer перехватывает эти исключения
- [ ] Пользователь получает понятное сообщение об ошибке
- [ ] Инбокс НЕ очищается при ошибках
- [ ] Backup сохраняется при всех типах ошибок
- [ ] Все тесты проходят

## Связанные файлы

- `utils/ollama_client.py` - Основной файл для изменений
- `handlers/summarizer.py` - Обработка ошибок
- `tests/unit/utils/test_ollama_client.py` - Тесты клиента
- `tests/integration/test_summarizer_integration.py` - Интеграционные тесты

## Примеры

### До исправления

```
20:55:57 - utils.ollama_client - ERROR - ❌ TimeoutException
21:00:57 - handlers.summarizer - INFO - → Результат: action=skip
21:00:57 - handlers.summarizer - WARNING - ⚠️ Ничего не создано, инбокс не очищается
```

**Проблема:** Пользователь не получил никакого сообщения.

### После исправления

```
20:55:57 - utils.ollama_client - ERROR - ❌ TimeoutException
21:00:57 - handlers.summarizer - ERROR - ❌ Таймаут LLM: Request timeout after 300s
21:00:58 - handlers.summarizer - INFO - Отправлено сообщение пользователю
```

**Результат:** Пользователь получил сообщение:
```
❌ Таймаут при обращении к LLM

💡 Ваши сообщения сохранены и будут обработаны позже.
🔄 Попробуйте /summarize снова через 5-10 минут.
```

## Примечания

- Не нужно менять timeout (он уже 300 секунд)
- Нужно только изменить поведение при ошибках
- Все существующие тесты должны продолжать проходить