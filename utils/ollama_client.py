import httpx
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from bot.config import settings
from bot.db.models import InboxMessage

logger = logging.getLogger(__name__)


class OpenAIConfig(BaseModel):
    base_url: str = settings.OLLAMA_BASE_URL
    model: str = settings.OLLAMA_MODEL


class OpenAIClient:
    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig()
        self.client = httpx.AsyncClient(base_url=self.config.base_url, timeout=300.0)

    async def summarize_group(self, messages: List[InboxMessage]) -> Dict[str, Any]:
        """Анализ группы сообщений через OpenAI-compatible API"""
        from datetime import datetime
        start_time = datetime.now()
        messages_text = self._format_messages(messages)

        if not messages_text.strip():
            logger.warning("⚠️ Empty messages text")
            return {"action": "skip", "reason": "Empty messages"}

        prompt = await self._build_prompt(messages_text)
        logger.info(f"📡 Отправка запроса в Ollama: {self.config.base_url}/chat/completions")
        logger.info(f"   Модель: {self.config.model}")
        logger.info(f"   Сообщений: {len(messages)}")
        logger.info(f"   Время отправки: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
        logger.info(f"   Таймаут: {self.client.timeout}")

        try:
            logger.info(f"📤 Отправка POST запроса...")
            logger.info(f"📤 Отправка POST запроса...")
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False
                }
            )
            logger.info(f"✅ Ответ получен, статус: {response.status_code}")
            logger.info(f"📦 Ответ (первые 500 символов): {response.text[:500]}")
            if response.status_code != 200:
                logger.error(f"❌ Ошибка ответа: {response.text[:200]}")
            response.raise_for_status()
            logger.info(f"📥 Парсинг JSON ответа...")
            result = response.json()
            raw_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"📥 Получен ответ от модели: {raw_response[:200]}...")
            parsed = self._parse_response(raw_response)
            logger.info(f"✅ Парсинг завершен: action={parsed.get('action')}, title={parsed.get('title', 'N/A')}")
            return parsed
        except httpx.ConnectError as e:
            logger.error(f"❌ ConnectError: {e}")
            return {"action": "skip", "reason": "API not available"}
        except httpx.TimeoutException as e:
            logger.error(f"❌ TimeoutException: {e}")
            return {"action": "skip", "reason": "Request timeout"}
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTPStatusError: {e.response.status_code} - {e.response.text[:200]}")
            return {"action": "skip", "reason": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Exception после {elapsed:.1f}с: {type(e).__name__}: {e}")
            return {"action": "skip", "reason": f"Error: {type(e).__name__}"}
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ Завершено через {elapsed:.1f}с")

    def _format_messages(self, messages: List[InboxMessage]) -> str:
        """Форматирование сообщений для промпта"""
        logger.debug(f"📝 Форматирование {len(messages)} сообщений для промпта")
        text = ""
        for msg in messages:
            sender = msg.sender_name or f"User {msg.sender_id}"
            text += f"[{msg.timestamp}] {sender}:\n{msg.content}\n\n"
        logger.debug(f"   Текст промпта ({len(text)} символов): {text[:100]}...")
        return text

    async def _build_prompt(self, messages_text: str) -> str:
        """Формирование промпта для анализа"""
        task_prompt = f"""Ты помощник для управления задачами. Проанализируй эти сообщения и преврати их в задачи если нужно.

{messages_text}

ПРАВИЛА:
1. Любое сообщение с просьбой, поручением, вопросом о действиях - это задача
2. Короткие сообщения тоже могут быть задачами
3. Вопросы с "сможешь", "сделаешь", "поможешь" - это задачи
4. Добавь до 3 тегов
5. Укажи все детали в content

ПРИМЕРЫ:

"А сушилку сможешь разобрать?..."
{{
  "action": "create_task",
  "title": "Разобрать сушилку",
  "tags": ["быт", "техника"],
  "content": "Разобрать сушилку по просьбе",
  "reason": "Просьба помочь разобрать технику"
}}

"Сможешь помочь с переездом?"
{{
  "action": "create_task",
  "title": "Помочь с переездом",
  "tags": ["помощь", "переезд"],
  "content": "Помочь с переездом по просьбе",
  "reason": "Просьба помочь с переездом"
}}

"Купи молока вечером"
{{
  "action": "create_task",
  "title": "Купить молока",
  "tags": ["покупки"],
  "content": "Купить молока вечером",
  "reason": "Поручение купить продукты"
}}

"Сделаешь мне отчет до пятницы?"
{{
  "action": "create_task",
  "title": "Подготовить отчет",
  "tags": ["работа", "дедлайн"],
  "content": "Подготовить отчет до пятницы",
  "reason": "Поручение подготовить отчет"
}}

"Запиши встречу на завтра в 14:00"
{{
  "action": "create_task",
  "title": "Встреча на завтра в 14:00",
  "tags": ["встреча", "календарь"],
  "content": "Записать встречу на завтра в 14:00",
  "reason": "Поручение записать встречу"
}}

"Это просто информация"
{{
  "action": "skip",
  "reason": "Это не задача, а просто информация"
}}

"Сегодня хорошая погода"
{{
  "action": "skip",
  "reason": "Это просто наблюдение, не задача"
}}

ФОРМАТ ОТВЕТА:
Если задача - верни:
{{
  "action": "create_task",
  "title": "Краткое название задачи",
  "tags": ["tag1", "tag2"],
  "content": "Полное описание",
  "reason": "Почему это задача"
}}

Если не задача - верни:
{{
  "action": "skip",
  "reason": "Почему это не задача"
}}
"""
        return task_prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Парсинг ответа модели"""
        import json

        logger.debug(f"🔍 Парсинг ответа модели: {response_text[:100]}...")
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            logger.debug(f"   JSON строка: {json_str[:100]}...")
            result = json.loads(json_str)
            logger.debug(f"✅ JSON распарсен: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return {"action": "skip"}