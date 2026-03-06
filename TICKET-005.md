# TICKET-005: Ollama интеграция

## Описание задачи
Реализовать клиент для запросов к локальной AI-модели Ollama для анализа групп сообщений и создания задач/заметок.

## Компоненты для реализации
- `utils/ollama_client.py` - OllamaClient для запросов к LLM

## Приоритет
🔴 Критический

## Критерии приёмки
- [ ] OllamaClient.summarize_group(messages) анализирует группу сообщений
- [ ] Возвращает JSON с решением: create_task, create_note, или skip
- [ ] Конфигурация BASE_URL: http://localhost:11434
- [ ] Моделируются промпты для задач и заметок
- [ ] Обработка ошибок при недоступности Ollama
- [ ] Поддержка настройки модели из .env (OLLAMA_MODEL)

## Технические детали

### utils/ollama_client.py
```python
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3"

class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.client = httpx.AsyncClient(base_url=self.config.base_url)
    
    async def summarize_group(self, messages: List[InboxMessage]) -> Dict[str, Any]:
        """Анализ группы сообщений через Ollama"""
        # Формирование текста группы
        messages_text = self._format_messages(messages)
        
        # Выбор промпта
        prompt = await self._build_prompt(messages_text)
        
        # Запрос к модели
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.config.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        result = response.json()
        return self._parse_response(result["response"])
    
    def _format_messages(self, messages: List[InboxMessage]) -> str:
        """Форматирование сообщений для промпта"""
        text = ""
        for msg in messages:
            sender = msg.sender_name or f"User {msg.sender_id}"
            text += f"[{msg.timestamp}] {sender}:\n{msg.content}\n\n"
        return text
    
    async def _build_prompt(self, messages_text: str) -> str:
        """Формирование промпта для анализа"""
        # Определяем, нужно ли создать задачу или заметку
        # Промпт для задач
        task_prompt = f"""Ты помощник для управления задачами. Проанализируй эти сообщения:

{messages_text}

Если есть действия, которые нужно выполнить:
- Создай задачу с чётким названием
- Добавь до 3 тегов
- Укажи все детали в content

Формат JSON:
{{
  "action": "create_task",
  "title": "Краткое название задачи",
  "tags": ["tag1", "tag2"],
  "content": "Полное описание",
  "reason": "Почему это задача"
}}

Если это не задача - верни: {{"action": "skip"}}
"""
        
        return task_prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Парсинг ответа модели"""
        import json
        
        # Извлечение JSON из ответа
        try:
            # Найти JSON в ответе
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            result = json.loads(json_str)
            return result
        except:
            return {"action": "skip"}
```

### Примеры использования
```python
# handlers/summarizer.py
client = OllamaClient(config)
result = await client.summarize_group(group)

if result["action"] == "create_task":
    task = Task(
        id=f"task_{len(tasks)+1:03d}",
        title=result["title"],
        tags=result["tags"],
        content=result["content"],
        source_message_ids=[m.id for m in group],
        created_at=datetime.now()
    )
    FileManager.append_task(user_id, task)

elif result["action"] == "create_note":
    note = Note(
        id=f"note_{len(notes)+1:03d}",
        title=result["title"],
        tags=result["tags"],
        content=result["content"],
        source_message_ids=[m.id for m in group],
        created_at=datetime.now()
    )
    FileManager.append_note(user_id, note)
```