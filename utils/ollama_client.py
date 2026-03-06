import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from bot.config import settings
from bot.db.models import InboxMessage


class OllamaConfig(BaseModel):
    base_url: str = settings.OLLAMA_BASE_URL
    model: str = settings.OLLAMA_MODEL


class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.client = httpx.AsyncClient(base_url=self.config.base_url, timeout=30.0)

    async def summarize_group(self, messages: List[InboxMessage]) -> Dict[str, Any]:
        """Анализ группы сообщений через Ollama"""
        messages_text = self._format_messages(messages)

        if not messages_text.strip():
            return {"action": "skip", "reason": "Empty messages"}

        prompt = await self._build_prompt(messages_text)

        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_response(result.get("response", ""))
        except httpx.ConnectError:
            return {"action": "skip", "reason": "Ollama not available"}
        except httpx.TimeoutException:
            return {"action": "skip", "reason": "Request timeout"}
        except httpx.HTTPStatusError as e:
            return {"action": "skip", "reason": f"HTTP error: {e.response.status_code}"}
        except Exception:
            return {"action": "skip", "reason": "Parsing error"}

    def _format_messages(self, messages: List[InboxMessage]) -> str:
        """Форматирование сообщений для промпта"""
        text = ""
        for msg in messages:
            sender = msg.sender_name or f"User {msg.sender_id}"
            text += f"[{msg.timestamp}] {sender}:\n{msg.content}\n\n"
        return text

    async def _build_prompt(self, messages_text: str) -> str:
        """Формирование промпта для анализа"""
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

        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            result = json.loads(json_str)
            return result
        except Exception:
            return {"action": "skip"}