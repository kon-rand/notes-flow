import sys
import pytest
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from bot.db.models import InboxMessage
from utils.ollama_client import OpenAIConfig, OpenAIClient
from utils.error_types import LLMTimeoutError, LLMNetworkError, LLMResponseError, LLMError
from typing import Optional


def create_message(id: str, offset_minutes: int, content: str, sender_name: str = "") -> InboxMessage:
    """Helper для создания тестовых сообщений"""
    return InboxMessage(
        id=id,
        timestamp=datetime(2026, 3, 6, 14, 0, 0) + timedelta(minutes=offset_minutes),
        from_user=123456789,
        sender_id=123456789,
        sender_name=sender_name,
        content=content,
        chat_id=-1001234567890
    )


def test_openai_config_default_model():
    """Тест: значение по умолчанию model"""
    config = OpenAIConfig()
    assert config.model == "unsloth/Qwen3.5-35B-A3B"


def test_openai_config_custom():
    """Тест: кастомная конфигурация"""
    config = OpenAIConfig(base_url="http://custom:11434", model="mistral")
    assert config.base_url == "http://custom:11434"
    assert config.model == "mistral"


def test_format_messages_basic():
    """Тест: базовое форматирование сообщений"""
    messages = [
        create_message("msg_1", 0, "Тестовое сообщение"),
    ]
    client = OpenAIClient()
    result = client._format_messages(messages)
    
    assert "Тестовое сообщение" in result
    assert "2026-03-06 14:00:00" in result


def test_format_messages_with_sender_name():
    """Тест: форматирование с sender_name"""
    messages = [
        create_message("msg_1", 0, "Привет", sender_name="Иван"),
    ]
    client = OpenAIClient()
    result = client._format_messages(messages)
    
    assert "Иван" in result


def test_format_messages_no_sender_name():
    """Тест: форматирование без sender_name"""
    messages = [
        create_message("msg_2", 10, "Без имени", sender_name=""),
    ]
    client = OpenAIClient()
    result = client._format_messages(messages)
    
    assert "User 123456789" in result


def test_format_messages_multiple():
    """Тест: несколько сообщений"""
    messages = [
        create_message("msg_1", 0, "Первое"),
        create_message("msg_2", 10, "Второе"),
        create_message("msg_3", 20, "Третье"),
    ]
    client = OpenAIClient()
    result = client._format_messages(messages)
    
    assert result.count("Первое") == 1
    assert result.count("Второе") == 1
    assert result.count("Третье") == 1


def test_format_messages_empty():
    """Тест: пустой список сообщений"""
    client = OpenAIClient()
    result = client._format_messages([])
    assert result == ""


def test_build_prompt_contains_messages():
    """Тест: промпт содержит текст сообщений"""
    messages_text = "[timestamp] User:\nТестовое сообщение"
    client = OpenAIClient()
    result = asyncio.run(client._build_prompt(messages_text))
    
    assert "Тестовое сообщение" in result


def test_build_prompt_contains_instructions():
    """Тест: промпт содержит инструкции"""
    messages_text = "Тест"
    client = OpenAIClient()
    result = asyncio.run(client._build_prompt(messages_text))
    
    assert "Сгруппируй" in result
    assert "JSON" in result


def test_build_prompt_skip_option():
    """Тест: опция skip в промпте"""
    messages_text = "Тест"
    client = OpenAIClient()
    result = asyncio.run(client._build_prompt(messages_text))
    
    # New prompt format uses JSON array
    assert '"action":' in result


def test_parse_valid_json():
    """Тест: парсинг валидного JSON"""
    client = OpenAIClient()
    # New format: JSON array
    json_str = '[{"action": "create_task", "title": "Тест", "tags": ["tag1"], "content": "Контент", "source_message_ids": []}]'
    result = client._parse_response(json_str)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["action"] == "create_task"
    assert result[0]["title"] == "Тест"
    assert result[0]["tags"] == ["tag1"]
    assert result[0]["content"] == "Контент"


def test_parse_json_with_prefix():
    """Тест: извлечение JSON из ответа с префиксом"""
    client = OpenAIClient()
    response = 'Ответ: [{"action": "create_task", "title": "Задача", "tags": [], "content": "", "source_message_ids": []}]'
    result = client._parse_response(response)
    
    assert isinstance(result, list)
    assert result[0]["action"] == "create_task"


def test_parse_json_with_suffix():
    """Тест: извлечение JSON из ответа с суффиксом"""
    client = OpenAIClient()
    response = 'Вот JSON: [{"action": "create_note", "title": "Заметка", "tags": [], "content": "", "source_message_ids": []}]'
    result = client._parse_response(response)
    
    assert isinstance(result, list)
    assert result[0]["action"] == "create_note"


def test_parse_invalid_json():
    """Тест: обработка некорректного формата"""
    client = OpenAIClient()
    result = client._parse_response("Это не JSON")
    
    assert result == []


def test_parse_empty_response():
    """Тест: пустой ответ"""
    client = OpenAIClient()
    result = client._parse_response("")
    
    assert result == []


def test_parse_partial_json():
    """Тест: частичный JSON (неполный ответ)"""
    client = OpenAIClient()
    result = client._parse_response('{"action": "create_task"')
    
    assert result == []


def test_parse_skip_action():
    """Тест: parse response с action=skip"""
    client = OpenAIClient()
    json_str = '[{"action": "skip", "reason": "Не важно"}]'
    result = client._parse_response(json_str)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["action"] == "skip"


@pytest.mark.asyncio
async def test_summarize_messages_successful_task():
    """Тест: успешный запрос к Ollama с create_task"""
    messages = [
        create_message("msg_1", 0, "Нужно подготовить отчёт"),
    ]
    
    mock_response = {
        "choices": [{"message": {"content": '[{"action": "create_task", "title": "Подготовить отчёт", "tags": ["работа"], "content": "Сделать отчёт", "source_message_ids": []}]'}}]
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert isinstance(result, list)
        assert result[0]["action"] == "create_task"
        assert result[0]["title"] == "Подготовить отчёт"
        assert mock_post.called


@pytest.mark.asyncio
async def test_summarize_messages_create_note():
    """Тест: возврат create_note"""
    messages = [
        create_message("msg_1", 0, "Сохрани идею: использовать async/await"),
    ]
    
    mock_response = {
        "choices": [{"message": {"content": '[{"action": "create_note", "title": "Идея async/await", "tags": ["идеи"], "content": "Использовать async/await", "source_message_ids": []}]'}}]
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert isinstance(result, list)
        assert result[0]["action"] == "create_note"
        assert mock_post.called


@pytest.mark.asyncio
async def test_summarize_messages_skip():
    """Тест: возврат skip"""
    messages = [
        create_message("msg_1", 0, "Просто сообщение"),
    ]
    
    mock_response = {"choices": [{"message": {"content": '[{"action": "skip"}]'}}]}
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert isinstance(result, list)
        assert result[0]["action"] == "skip"
        assert mock_post.called


@pytest.mark.asyncio
async def test_summarize_messages_connect_error():
    """Тест: обработка httpx.ConnectError (Ollama недоступен)"""
    messages = [
        create_message("msg_1", 0, "Тест"),
    ]
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert result == []


@pytest.mark.asyncio
async def test_summarize_messages_timeout():
    """Тест: обработка httpx.TimeoutException (timeout)"""
    messages = [
        create_message("msg_1", 0, "Тест"),
    ]
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert result == []


@pytest.mark.asyncio
async def test_summarize_messages_http_error():
    """Тест: обработка некорректного ответа (status_code != 200)"""
    messages = [
        create_message("msg_1", 0, "Тест"),
    ]
    
    mock_response = MagicMock(status_code=500)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=mock_response)
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert result == []


@pytest.mark.asyncio
async def test_summarize_messages_empty_messages():
    """Тест: пустая группа сообщений"""
    client = OpenAIClient()
    result = await client.summarize_messages([])
    
    assert result == []


@pytest.mark.asyncio
async def test_summarize_messages_custom_config():
    """Тест: использование кастомной конфигурации"""
    messages = [
        create_message("msg_1", 0, "Тест"),
    ]
    
    mock_response = {"choices": [{"message": {"content": '[{"action": "skip"}]'}}]}
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        config = OpenAIConfig(base_url="http://custom:11434", model="test-model")
        client = OpenAIClient(config=config)
        await client.summarize_messages(messages)
        
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "test-model"


@pytest.mark.asyncio
async def test_summarize_messages_long_messages():
    """Тест: очень длинные сообщения"""
    long_content = "Это очень длинное сообщение " * 100
    messages = [
        create_message("msg_1", 0, long_content),
    ]
    
    mock_response = {"choices": [{"message": {"content": '[{"action": "skip"}]'}}]}
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert isinstance(result, list)
        assert result[0]["action"] == "skip"


@pytest.mark.asyncio
async def test_summarize_messages_multiple_messages():
    """Тест: несколько сообщений в группе"""
    messages = [
        create_message("msg_1", 0, "Первое сообщение"),
        create_message("msg_2", 5, "Второе сообщение"),
        create_message("msg_3", 10, "Третье сообщение"),
    ]
    
    mock_response = {
        "choices": [{"message": {"content": '[{"action": "create_task", "title": "Обработка нескольких сообщений", "tags": ["test"], "content": "Контент", "source_message_ids": []}]'}}]
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=mock_response),
            raise_for_status=MagicMock()
        )
        
        client = OpenAIClient()
        result = await client.summarize_messages(messages)
        
        assert isinstance(result, list)
        assert result[0]["action"] == "create_task"
