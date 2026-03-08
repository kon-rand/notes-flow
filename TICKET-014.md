# TICKET-014: Интеграционный тест саммаризации

## Описание задачи

Создать интеграционный тест, который проверяет полную цепочку саммаризации:
1. Загрузка реальных данных из инбокса
2. Вызов LLM через Ollama
3. Создание задачи на основе ответа LLM
4. Проверка что задача корректно сохранена

## Компоненты для реализации

- Интеграционный тест с реальным вызовом LLM
- Тестовые данные из текущего инбокса
- Валидация created задач
- Проверка корректности парсинга ответа LLM

## Приоритет

🔴 Высокий

## Критерии приёмки

- [ ] Тест загружает данные из реального инбокса пользователя
- [ ] Тест вызывает Ollama API с реальными данными
- [ ] Тест проверяет что задача создана после саммаризации
- [ ] Тест проверяет корректность парсинга JSON ответа LLM
- [ ] Тест выполняется в изолированной среде (не влияет на production данные)
- [ ] Тест показывает полный лог запроса/ответа LLM
- [ ] Тест падает если LLM возвращает некорректный ответ

## Технические детали

### Структура теста

```python
# tests/integration/test_summarizer.py

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage, Task
from utils.ollama_client import OpenAIClient
from handlers.summarizer import auto_summarize


@pytest.mark.integration
class TestSummarizerIntegration:
    """Интеграционные тесты саммаризации"""
    
    TEST_USER_ID = 999999  # Изолированный тестовый пользователь
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Подготовка и очистка тестовых данных"""
        file_manager = FileManager()
        
        # Очистка перед тестом
        file_manager.clear_messages(self.TEST_USER_ID)
        
        yield
        
        # Очистка после теста
        file_manager.clear_messages(self.TEST_USER_ID)
    
    def test_load_messages_from_inbox(self):
        """Тест загрузки сообщений из инбокса"""
        # Создаём тестовые сообщения
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=self.TEST_USER_ID,
                sender_id=self.TEST_USER_ID,
                sender_name="Test User",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            ),
            InboxMessage(
                id="msg_002",
                timestamp=datetime.now(),
                from_user=self.TEST_USER_ID,
                sender_id=self.TEST_USER_ID,
                sender_name="Test User",
                content="Да, конечно",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(self.TEST_USER_ID, msg)
        
        # Загружаем обратно
        loaded = file_manager.read_messages(self.TEST_USER_ID)
        
        assert len(loaded) == 2
        assert loaded[0].content == "А сушилку сможешь разобрать?"
    
    @pytest.mark.asyncio
    async def test_ollama_api_call(self):
        """Тест вызова Ollama API с реальными данными"""
        from utils.context_analyzer import ContextAnalyzer
        
        # Подготавливаем сообщения
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=self.TEST_USER_ID,
                sender_id=self.TEST_USER_ID,
                sender_name="Test User",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            )
        ]
        
        # Группируем сообщения
        analyzer = ContextAnalyzer()
        groups = analyzer.group_messages(messages)
        
        # Вызываем Ollama
        client = OpenAIClient()
        result = await client.summarize_group(groups[0])
        
        # Проверяем что ответ парсится корректно
        assert "action" in result
        assert result["action"] in ["create_task", "create_note", "skip"]
        
        # Логируем полный ответ для отладки
        print(f"\n=== Ollama Response ===")
        print(f"Action: {result.get('action')}")
        print(f"Title: {result.get('title')}")
        print(f"Tags: {result.get('tags')}")
        print(f"Content: {result.get('content')}")
        print(f"======================\n")
    
    @pytest.mark.asyncio
    async def test_full_summarization_flow(self):
        """Тест полной цепочки саммаризации"""
        from aiogram import Bot
        
        # Создаём тестовые сообщения (как в реальном инбоксе)
        messages = [
            InboxMessage(
                id="msg_001",
                timestamp=datetime.now(),
                from_user=self.TEST_USER_ID,
                sender_id=self.TEST_USER_ID,
                sender_name="Тест",
                content="А сушилку сможешь разобрать?",
                chat_id=-1001234567890
            )
        ]
        
        file_manager = FileManager()
        for msg in messages:
            file_manager.append_message(self.TEST_USER_ID, msg)
        
        # Проверяем что сообщения сохранены
        loaded = file_manager.read_messages(self.TEST_USER_ID)
        assert len(loaded) == 1
        
        # Запускаем саммаризацию
        bot = Bot(token="test_token")  # Test bot, will fail on send but that's ok
        result = await auto_summarize(self.TEST_USER_ID, bot)
        
        # Проверяем результат
        assert "error" not in result or result.get("error") is None
        
        # Проверяем что задача создана
        tasks = file_manager.read_tasks(self.TEST_USER_ID)
        assert len(tasks) > 0
        
        # Проверяем что инбокс очищен
        inbox = file_manager.read_messages(self.TEST_USER_ID)
        assert len(inbox) == 0
        
        # Логируем созданную задачу
        print(f"\n=== Created Task ===")
        for task in tasks:
            print(f"ID: {task.id}")
            print(f"Title: {task.title}")
            print(f"Tags: {task.tags}")
            print(f"==================\n")
    
    def test_current_inbox_data(self):
        """Тест с реальными данными из текущего инбокса"""
        # Загружаем данные из реального инбокса пользователя 61395267
        file_manager = FileManager()
        real_messages = file_manager.read_messages(61395267)
        
        if not real_messages:
            pytest.skip("Нет данных в инбоксе для тестирования")
        
        print(f"\n=== Real Inbox Data ===")
        print(f"User ID: 61395267")
        print(f"Messages count: {len(real_messages)}")
        for msg in real_messages:
            print(f"- {msg.id}: {msg.content[:100]}...")
        print(f"=======================\n")
        
        # Проверяем что данные загружены
        assert len(real_messages) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

### Пример ожидаемого вывода LLM

```json
{
  "action": "create_task",
  "title": "Разобрать сушилку",
  "tags": ["быт", "техника"],
  "content": "Пользователь спрашивает, смогу ли я разобрать сушилку."
}
```

### Запуск теста

```bash
# Запустить все интеграционные тесты
pytest tests/integration/test_summarizer.py -v -s

# Запустить только тест с Ollama
pytest tests/integration/test_summarizer.py::TestSummarizerIntegration::test_ollama_api_call -v -s

# Запустить полный flow
pytest tests/integration/test_summarizer.py::TestSummarizerIntegration::test_full_summarization_flow -v -s
```

### Требования к окружению

- Ollama запущен и доступен по `http://127.0.0.1:8080`
- Модель `unsloth/Qwen3.5-35B-A3B` загружена
- Переменные окружения `.env` настроены корректно

### Troubleshooting

Если тест падает с ошибкой подключения к Ollama:

```bash
# Проверить что Ollama запущен
curl http://127.0.0.1:8080/models

# Проверить что модель загружена
docker ps | grep ollama

# Перезапустить контейнер
docker-compose -f docker-compose.local.yml restart
```

## Примечания

- Тесты должны выполняться в изоляции (отдельный user_id)
- Все тестовые данные должны очищаться после теста
- При работе с реальными данными (user_id=61395267) делать бэкап перед тестом
- Логировать полный запрос/ответ для отладки проблем с LLM