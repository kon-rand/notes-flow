# TICKET-013: Исправление обработки ошибок при таймауте LLM

## Описание задачи

При запросе к LLM, который падает по таймауту, сообщения из инбокса теряются. Необходимо:
1. Не очищать инбокс при ошибках (таймаут, сетевые ошибки, ошибки модели)
2. Выводить понятную ошибку пользователю в чат
3. Сохранять backup перед возвратом ошибки

## Текущая проблема

В `handlers/summarizer.py:136-147` функция `auto_summarize` перехватывает все исключения, но:
- Сообщения из инбокса НЕ очищаются при ошибке (это хорошо)
- Однако backup создается, но сообщения остаются в инбоксе
- Пользователь не понимает, что произошло
- При следующем `/summarize` те же сообщения будут пытаться обработаться снова

## Требования

### 1. Разделение типов ошибок

В `handlers/summarizer.py:136` нужно разделить обработку ошибок:

**Критические ошибки (инбокс НЕ очищать):**
- Таймаут запроса к LLM
- Сетевые ошибки (connection error, timeout)
- Ошибки парсинга ответа LLM
- Ошибки модели (invalid response format)

**Успешная обработка (инбокс очищать):**
- LLM вернула ответ, но action=skip для всех групп
- В этом случае сообщения можно считать "обработанными" (даже если пропущенными)

### 2. Улучшение сообщений об ошибках

При критических ошибках отправлять пользователю:

```
❌ Ошибка при саммаризации: [детали ошибки]

💡 Ваши сообщения сохранены и будут обработаны позже.
🔄 Попробуйте /summarize снова через несколько минут.

Если проблема повторится, проверьте:
- Стабильность интернет-соединения
- Доступность LLM сервера
```

### 3. Логирование

Добавить детальное логирование для всех типов ошибок:

```python
# В обработчике ошибок
logger.error(f"❌ Критическая ошибка при саммаризации: {error_type}: {str(e)}")
logger.error(f"   Сообщений в инбоксе: {len(messages)}")
logger.error(f"   ID сообщений: {[m.id for m in messages]}")
logger.error(f"   Stack trace: {traceback.format_exc()}")
```

### 4. Тестирование

Создать тесты для всех сценариев ошибок:

1. **test_summarizer_timeout_error** - Таймаут запроса к LLM
2. **test_summarizer_network_error** - Сетевая ошибка
3. **test_summarizer_invalid_response** - Неверный формат ответа LLM
4. **test_summarizer_success_with_skip** - Успешная обработка, все пропущено
5. **test_summarizer_error_inbox_preserved** - При ошибке инбокс не очищается

## Технические детали

### Пример кода для обработки ошибок

```python
import traceback
from urllib3.exceptions import MaxRetryError, ReadTimeoutError
import requests.exceptions

async def auto_summarize(user_id: int, bot: Optional[Bot] = None):
    # ... код до try ...
    
    try:
        # Основная логика
        for i, group in enumerate(groups, 1):
            result = await client.summarize_group(group)
            # ... обработка результата ...
    
    except (ReadTimeoutError, requests.exceptions.Timeout, asyncio.TimeoutError) as e:
        logger.error(f"❌ Таймаут запроса к LLM: {str(e)}")
        if bot:
            await bot.send_message(user_id, 
                "❌ Таймаут при обращении к LLM\n\n"
                "💡 Ваши сообщения сохранены и будут обработаны позже.\n"
                "🔄 Попробуйте /summarize снова через 5-10 минут."
            )
        return {"error": "timeout", "message": "timeout"}
    
    except MaxRetryError as e:
        logger.error(f"❌ Сетевая ошибка: {str(e)}")
        if bot:
            await bot.send_message(user_id,
                "❌ Сетевая ошибка при обращении к LLM\n\n"
                "💡 Проверьте соединение и попробуйте снова."
            )
        return {"error": "network", "message": str(e)}
    
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {type(e).__name__}: {str(e)}")
        logger.error(f"   Stack: {traceback.format_exc()}")
        if bot:
            await bot.send_message(user_id,
                f"❌ Ошибка: {str(e)}\n\n"
                "💡 Ваши сообщения сохранены.\n"
                "🔄 Попробуйте /summarize снова."
            )
        return {"error": "unknown", "message": str(e)}
```

### Классификация ошибок

Создать enum для типов ошибок:

```python
from enum import Enum

class SummarizationErrorType(Enum):
    TIMEOUT = "timeout"
    NETWORK = "network"
    INVALID_RESPONSE = "invalid_response"
    PARSING_ERROR = "parsing_error"
    UNKNOWN = "unknown"
```

## Приоритет

🔴 **Высокий** - Критично для UX, пользователи теряют данные

## Критерии приемки

- [ ] При таймауте LLM инбокс НЕ очищается
- [ ] Пользователь получает понятное сообщение об ошибке
- [ ] Backup сохраняется при всех типах ошибок
- [ ] Все сообщения логируются с деталями
- [ ] Тесты покрывают все сценарии ошибок
- [ ] При успешной обработке (даже с action=skip) инбокс очищается
- [ ] После исправления ошибки пользователь может повторить `/summarize`

## Связанные файлы

- `handlers/summarizer.py` - Основная логика обработки
- `utils/ollama_client.py` - Клиент для запросов к LLM
- `tests/integration/test_summarizer_integration.py` - Интеграционные тесты
- `tests/unit/utils/test_ollama_client.py` - Тесты клиента

## Примеры ошибок

### Таймаут (сейчас 120s, нужно увеличить до 300s)
```
ReadTimeoutError: HTTPSConnectionPool(host='127.0.0.1', port=8080): 
Read timed out. (timeout=120.0)
```

### Сетевая ошибка
```
MaxRetryError: HTTPSConnectionPool(host='127.0.0.1', port=8080): 
Max retries exceeded with url: /chat/completions 
(Caused by NewConnectionError(...))
```

### Неверный формат ответа
```
JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2
```

## Примечания

- Увеличить timeout в `utils/ollama_client.py` с 120 до 300 секунд
- Рассмотреть возможность реализации retry-механизма с экспоненциальной задержкой
- Добавить метрики для отслеживания частоты ошибок