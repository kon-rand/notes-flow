import logging
from typing import Dict, Any

import httpx

from bot.config import settings
from utils.ollama_client import OpenAIClient

logger = logging.getLogger(__name__)


async def healthcheck() -> Dict[str, Any]:
    """Проверка здоровья приложения и подключения к AI API"""
    result = {
        "status": "healthy",
        "checks": {}
    }
    
    # Проверка подключения к AI API
    try:
        async with httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=5.0
        ) as client:
            response = await client.get("/models")
            if response.status_code == 200:
                result["checks"]["ai_api"] = {
                    "status": "healthy",
                    "base_url": settings.OLLAMA_BASE_URL
                }
            else:
                result["checks"]["ai_api"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                result["status"] = "degraded"
    except Exception as e:
        result["checks"]["ai_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        result["status"] = "unhealthy"
    
    return result


async def ping() -> Dict[str, Any]:
    """Проверка подключения к AI модели"""
    client = OpenAIClient()
    
    try:
        # Пробный запрос к API
        async with client.client as http_client:
            response = await http_client.get("/models")
            response.raise_for_status()
            
            models_data = response.json()
            models = models_data.get("data", [])
            model_names = [m.get("id", "unknown") for m in models]
            
            return {
                "status": "ok",
                "message": "AI API connected",
                "available_models": model_names,
                "config": {
                    "base_url": settings.OLLAMA_BASE_URL,
                    "model": settings.OLLAMA_MODEL
                }
            }
    except Exception as e:
        logger.error(f"❌ Ping failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "config": {
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL
            }
        }