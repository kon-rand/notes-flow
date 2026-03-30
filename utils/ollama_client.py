import httpx
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from bot.config import settings
from bot.db.models import InboxMessage
from utils.error_types import LLMError, LLMTimeoutError, LLMNetworkError, LLMResponseError

logger = logging.getLogger(__name__)


class OpenAIConfig(BaseModel):
    base_url: str = settings.OLLAMA_BASE_URL
    model: str = settings.OLLAMA_MODEL


class OpenAIClient:
    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig()
        self.client = httpx.AsyncClient(base_url=self.config.base_url, timeout=300.0)

    async def summarize_messages(self, messages: List[InboxMessage]) -> List[Dict[str, Any]]:
        """Анализ списка сообщений через OpenAI-compatible API.
        
        Возвращает список задач/заметок (может быть 0, 1 или несколько).
        LLM сам определяет группировку по времени и семантике.
        """
        from datetime import datetime
        start_time = datetime.now()
        messages_text = self._format_messages(messages)

        if not messages_text.strip():
            logger.warning("⚠️ Empty messages text")
            return []

        prompt = await self._build_prompt(messages_text)
        logger.info(f"📡 Отправка запроса в Ollama: {self.config.base_url}/chat/completions")
        logger.info(f"   Модель: {self.config.model}")
        logger.info(f"   Сообщений: {len(messages)}")
        logger.info(f"   Время отправки: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
        logger.info(f"   Таймаут: {self.client.timeout}")

        try:
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
            logger.info(f"✅ Парсинг завершен: {len(parsed)} задач/заметок")
            return parsed
        except httpx.ConnectError as e:
            logger.error(f"❌ ConnectError: {e}")
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ Завершено через {elapsed:.1f}с")
            return []
        except httpx.TimeoutException as e:
            logger.error(f"❌ TimeoutException: {e}")
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ Завершено через {elapsed:.1f}с")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTPStatusError: {e.response.status_code} - {e.response.text[:200]}")
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ Завершено через {elapsed:.1f}с")
            return []
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Exception после {elapsed:.1f}с: {type(e).__name__}: {e}")
            logger.info(f"⏱️ Завершено через {elapsed:.1f}с")
            return []

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
        """Формирование промпта для анализа.
        
        LLM должен сам определить группировку по времени и семантике,
        и вернуть список всех задач/заметок в одном ответе.
        """
        task_prompt = f"""Ты помощник для управления задачами. Проанализируй эти сообщения и создай задачи если нужно.

{messages_text}

       ВАЖНО:
1. Сгруппируй сообщения по автору (диалоги) и времени (до 5 минут)
2. Сообщения от разных авторов НЕ группируй вместе, если это не явный диалог
3. Верни ВСЕ задачи и заметки в одном ответе в формате JSON массива
4. Любое сообщение с просьбой, поручением, вопросом о действиях - это задача
5. Короткие сообщения тоже могут быть задачами
6. Вопросы с "сможешь", "сделаешь", "поможешь" - это задачи
7. Добавь до 3 тегов на задачу
8. Укажи все детали в content
9. ЗАГОЛОВОК ЗАДАЧИ должен быть КОНКРЕТНЫМ и ACTION-ориентированным:
   - Использовать глаголы: "Добавить", "Написать", "Подготовить", "Исправить", "Проверить"
   - Включать упоминания людей через @username в заголовок
   - Включать пути к файлам в заголовок
   - Кратко, но информативно (не более 10-12 слов)

КРИТИЧЕСКИ ВАЖНО - ИЗВЛЕЧЕНИЕ КОНКРЕТНЫХ ДЕЙСТВИЙ:
- НЕ переформулируй текст сообщения в заголовок
- НЕ используй вводные фразы типа "Кость, я тут..." или "Справишься?"
- ИЗВЛЕКАЙ конкретное действие из сообщения (глагол: "написать", "подготовить", "купить", "разобрать")
- НЕ создавай задачи типа "уточнить детали", "обсудить", "проверить" - это не конкретные действия
- Если есть конкретное действие (написать самоотзыв, купить хлеб, разобрать сушилку) - используй ЕГО
- Включай сроки в заголовок если они есть (например "к 8му апреля" → "к 8-му апреля")
- Если сообщение содержит ссылку на формат/пример, включи её в content, а не в title

КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ ССЫЛОК НА ТИКЕТЫ:
- Если в тексте есть номер тикета (например "LAVKAINCIDENTS-1575" или "TICKET-123"), извлеки его
- В поле content добавь ссылку в формате Markdown: [ТИКЕТ-НОМЕР](https://st.yandex-team.ru/ТИКЕТ-НОМЕР)
- Пример: если в тексте "Тикет: LAVKAINCIDENTS-1575", добавь в content: "Ссылка на тикет: [LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)"
- Если тикет упоминается в контексте задачи (например "Нужно заполнить инцидент"), включи ссылку в заголовок задачи

"Кость, я тут в отпуск подумал походить, есть домашнее задание для тебя 🙈️️️️️️

Самоотзыв за три месяца работы в фидбечницу написать, формат как обычно, ревьюшный, типа https://wiki.yandex-team.ru/lavka/dev/samootzyv-dev-062025/ .

Справишься? К 8му апреля получается в твоем случае )"
→ [{{"action": "create_task", "title": "Написать самоотзыв к 8-му апреля @Maxim Tokarev", "tags": ["assignment", "vacation", "priority"], "content": "Написать самоотзыв в фидбечницу за три месяца работы. Формат ревьюшный: https://wiki.yandex-team.ru/lavka/dev/samootzyv-dev-062025/", "reason": "Максим Tokarev уезжает в отпуск и передает домашнее задание Константину Zakhmatov. КОНКРЕТНОЕ ДЕЙСТВИЕ: написать самоотзыв, а не уточнять детали!"}}]

"А сушилку сможешь разобрать?"
→ [{{"action": "create_task", "title": "Разобрать сушилку", "tags": ["быт", "техника"], "content": "Разобрать сушилку по просьбе", "reason": "Просьба помочь разобрать технику"}}]

"Купи молока вечером. Ещё хлеба нужно."
→ [{{"action": "create_task", "title": "Купить продукты", "tags": ["покупки"], "content": "Купить молока и хлеба вечером", "reason": "Поручение купить продукты"}}]

"Нужно подготовить отчёт. Вот данные: [ссылка]. Как я говорил, ещё добавь статистику."
→ [{{"action": "create_task", "title": "Подготовить отчёт по проекту", "tags": ["работа", "отчёт"], "content": "Собрать данные из файла, добавить статистику, сдать до завтра 10:00", "reason": "Поручение подготовить отчёт с данными и статистикой"}}]

"Купи хлеба" (от пользователя А)
"Сколько хлеба нужно?" (от пользователя Б)
"2 кило" (от пользователя А)
→ [{{"action": "create_task", "title": "Купить 2 кг хлеба", "tags": ["покупки"], "content": "Купить 2 кг хлеба по просьбе", "reason": "Диалог о покупке хлеба"}}]

"привет, в файле taskrouter/doc/api/models/user_activity.yaml нет required, это правильно? там больше обязательных полей, но часть из них просто nullable добавишь плиз, как время будет"
→ [{{"action": "create_task", "title": "Добавить required поля в user_activity.yaml и написать Арине @ease_l", "tags": ["api", "yaml", "документация"], "content": "Arina заметила отсутствие required в файле taskrouter/doc/api/models/user_activity.yaml. Добавить обязательные поля (user_id, role_ids и другие). Написать Arine @ease_l, что задача взята в работу", "reason": "Arina попросила добавить required поля в YAML файл"}}]

"Нужно заполнить инцидент. Уровень: green. Описание: Части товаров кухни нет на фронте. Тикет: LAVKAINCIDENTS-1575"
→ [{{"action": "create_task", "title": "Заполнить инцидент [LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)", "tags": ["инцидент", "lavka"], "content": "Уровень: green. Описание: Части товаров кухни нет на фронте. Ссылка на тикет: [LAVKAINCIDENTS-1575](https://st.yandex-team.ru/LAVKAINCIDENTS-1575)", "reason": "Поручение заполнить инцидент с номером LAVKAINCIDENTS-1575"}}]

"Это просто информация. Сегодня хорошая погода."
→ [] (пустой массив, если нет задач)

ФОРМАТ ОТВЕТА:
Верни JSON массив, где каждый элемент - это задача или заметка:

[
  {{
    "action": "create_task",
    "title": "Краткое название задачи",
    "tags": ["tag1", "tag2"],
    "content": "Полное описание",
    "reason": "Почему это задача"
  }},
  {{
    "action": "create_note",
    "title": "Название заметки",
    "tags": ["tag1"],
    "content": "Контент заметки",
    "reason": "Почему это стоит сохранить"
  }}
]

Если нет задач - верни пустой массив: []
"""
        return task_prompt

    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Парсинг ответа модели.
        
        Ожидаем JSON массив задач/заметок или пустой массив.
        """
        import json

        logger.debug(f"🔍 Парсинг ответа модели: {response_text[:100]}...")
        try:
            # Пытаемся найти массив [...]
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            
            if start == -1 or end == 0:
                # Если массива нет, пытаемся найти объект {} (старый формат)
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > 0:
                    json_str = response_text[start:end]
                    logger.debug(f"   JSON объект (старый формат): {json_str[:100]}...")
                    result = json.loads(json_str)
                    # Конвертируем в массив для совместимости
                    logger.debug(f"✅ JSON распарсен (объект): {result}")
                    return [result]
                
                logger.error(f"❌ Не найден ни массив, ни объект в ответе")
                return []
            
            json_str = response_text[start:end]
            logger.debug(f"   JSON массив: {json_str[:100]}...")
            result = json.loads(json_str)
            
            # Гарантируем что всегда возвращаем список
            if not isinstance(result, list):
                logger.warning(f"⚠️ Ожидался массив, получен {type(result).__name__}, конвертируем")
                result = [result]
            
            logger.debug(f"✅ JSON распарсен: {len(result)} элементов")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSONDecodeError: {e}")
            logger.error(f"   Текст ответа: {response_text[:200]}")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return []