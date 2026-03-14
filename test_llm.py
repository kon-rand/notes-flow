#!/usr/bin/env python3
"""Тестирование подключения к LLM через OpenAI-compatible API"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_llm_connection():
    """Тестирование подключения к LLM"""
    base_url = "http://127.0.0.1:8080"
    
    logger.info(f"🔍 Testing LLM connection at {base_url}")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Тест 1: Получение списка моделей
        logger.info("\n📋 Test 1: GET /models")
        try:
            response = await client.get("/models")
            logger.info(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                logger.info(f"   ✅ Models found: {len(models)}")
                for model in models:
                    logger.info(f"      - {model.get('id', 'N/A')}")
            else:
                logger.error(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
        
        # Тест 2: Отправка запроса к чату
        logger.info("\n💬 Test 2: POST /chat/completions")
        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": "unsloth/Qwen3.5-35B-A3B",
                    "messages": [{"role": "user", "content": "Hello, are you there?"}],
                    "stream": False
                }
            )
            logger.info(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"   ✅ Response: {content[:100]}...")
            else:
                logger.error(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
    
    logger.info("\n✅ Testing complete")


if __name__ == "__main__":
    asyncio.run(test_llm_connection())