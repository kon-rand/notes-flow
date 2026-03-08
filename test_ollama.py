#!/usr/bin/env python3
"""Проверка соединения с Ollama"""

import asyncio
import httpx
from bot.config import settings


async def test_ollama():
    """Проверка соединения с Ollama"""
    base_url = settings.OLLAMA_BASE_URL
    model = settings.OLLAMA_MODEL
    
    print(f"Testing Ollama connection...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Test 1: Check if endpoint is reachable
        try:
            print("\n1. Testing /api/generate endpoint...")
            response = await client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": "Hello",
                    "stream": False
                }
            )
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.json()}")
        except httpx.ConnectError as e:
            print(f"❌ Connection error: {e}")
            return False
        except httpx.TimeoutException:
            print(f"❌ Timeout error")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    # Test 2: Test with actual message
    try:
        print("\n2. Testing with message 'А сушилку сможешь разобрать?'...")
        response = await client.post(
            "/api/generate",
            json={
                "model": model,
                "prompt": """Ты помощник для управления задачами. Проанализируй эти сообщения и преврати их в задачи если нужно.

[2024-01-15 14:30:00] User:
А сушилку сможешь разобрать?

ПРАВИЛА:
1. Любое сообщение с просьбой, поручением, вопросом о действиях - это задача
2. Короткие сообщения тоже могут быть задачами
3. Вопросы с "сможешь", "сделаешь", "поможешь" - это задачи
4. Добавь до 3 тегов
5. Укажи все детали в content

ФОРМАТ ОТВЕТА (JSON):
{
  "action": "create_task",
  "title": "Краткое название задачи",
  "tags": ["tag1", "tag2"],
  "content": "Полное описание",
  "reason": "Почему это задача"
}

Или если не задача:
{
  "action": "skip",
  "reason": "Почему это не задача"
}""",
                "stream": False
            }
        )
        print(f"Status code: {response.status_code}")
        result = response.json()
        print(f"Raw response: {result.get('response', '')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    print(f"\n{'✅ Test passed' if result else '❌ Test failed'}")