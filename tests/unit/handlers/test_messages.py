import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from aiogram.types import User, Chat
from aiogram.types.message_origin_user import MessageOriginUser
from aiogram.types.message_origin_hidden_user import MessageOriginHiddenUser
from aiogram.types.message_origin_chat import MessageOriginChat
from bot.db.models import InboxMessage
from handlers.messages import extract_forward_info, message_handler


@pytest.fixture
def sample_forward_user():
    """Mock MessageOriginUser"""
    sender_user = User(id=987654321, first_name="Original", last_name="Sender", is_bot=False)
    return MessageOriginUser(date=datetime.now(), sender_user=sender_user)


@pytest.fixture
def sample_forward_hidden_user():
    """Mock MessageOriginHiddenUser"""
    return MessageOriginHiddenUser(date=datetime.now(), sender_user_name="Hidden User")


@pytest.fixture
def sample_forward_chat():
    """Mock MessageOriginChat"""
    sender_chat = Chat(id=-1001234567890, type="channel", title="News Channel")
    return MessageOriginChat(date=datetime.now(), sender_chat=sender_chat)


@pytest.fixture
def mock_message_no_forward():
    """Mock message without forward"""
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Test", last_name="User", is_bot=False)
    msg.to = None
    msg.forward_origin = None
    msg.message_id = 1
    msg.date = datetime.now()
    msg.text = "Test message"
    msg.caption = None
    msg.to = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_user(sample_forward_user):
    """Mock message with MessageOriginUser"""
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = sample_forward_user
    msg.message_id = 2
    msg.date = datetime.now()
    msg.text = "Forwarded message"
    msg.caption = None
    msg.to = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_hidden_user(sample_forward_hidden_user):
    """Mock message with MessageOriginHiddenUser"""
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = sample_forward_hidden_user
    msg.message_id = 3
    msg.date = datetime.now()
    msg.text = "Hidden forwarded message"
    msg.caption = None
    msg.to = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_chat(sample_forward_chat):
    """Mock message with MessageOriginChat"""
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = sample_forward_chat
    msg.message_id = 4
    msg.date = datetime.now()
    msg.text = "Chat forwarded message"
    msg.caption = None
    msg.to = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_hidden_no_name():
    """Mock message with MessageOriginHiddenUser without name"""
    forward = MessageOriginHiddenUser(date=datetime.now(), sender_user_name="")
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = forward
    msg.message_id = 5
    msg.date = datetime.now()
    msg.text = "Forwarded without sender"
    msg.caption = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_chat_no_title():
    """Mock message with MessageOriginChat without title"""
    sender_chat = Chat(id=-1001234567890, type="channel", title=None)
    forward = MessageOriginChat(date=datetime.now(), sender_chat=sender_chat)
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = forward
    msg.message_id = 6
    msg.date = datetime.now()
    msg.text = "Forwarded without title"
    msg.caption = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


@pytest.fixture
def mock_message_forward_caption():
    """Mock message with caption instead of text"""
    sender_user = User(id=987654321, first_name="Photo", last_name="Sender", is_bot=False)
    forward = MessageOriginUser(date=datetime.now(), sender_user=sender_user)
    
    msg = AsyncMock()
    msg.from_user = User(id=123456789, first_name="Forwarder", last_name="User", is_bot=False)
    msg.forward_origin = forward
    msg.message_id = 7
    msg.date = datetime.now()
    msg.text = None
    msg.caption = "Photo caption"
    msg.to = None
    msg.chat = MagicMock()
    msg.chat.id = 123456789
    return msg


def test_extract_forward_info_no_forward():
    """Test: extract_forward_info для сообщения без пересылки"""
    msg = AsyncMock()
    msg.forward_origin = None
    
    result = extract_forward_info(msg)
    assert result is None


def test_extract_forward_info_user(sample_forward_user):
    """Test: extract_forward_info для MessageOriginUser"""
    msg = AsyncMock()
    msg.forward_origin = sample_forward_user
    
    result = extract_forward_info(msg)
    
    assert result is not None
    sender_id, sender_name = result
    assert sender_id == 987654321
    assert sender_name == "Original Sender"


def test_extract_forward_info_hidden_user(sample_forward_hidden_user):
    """Test: extract_forward_info для MessageOriginHiddenUser"""
    msg = AsyncMock()
    msg.forward_origin = sample_forward_hidden_user
    
    result = extract_forward_info(msg)
    
    assert result is not None
    sender_id, sender_name = result
    assert sender_id == 0
    assert sender_name == "Hidden User"


def test_extract_forward_info_chat(sample_forward_chat):
    """Test: extract_forward_info для MessageOriginChat"""
    msg = AsyncMock()
    msg.forward_origin = sample_forward_chat
    
    result = extract_forward_info(msg)
    
    assert result is not None
    sender_id, sender_name = result
    assert sender_id == -1001234567890
    assert sender_name == "News Channel"


def test_extract_forward_info_hidden_user_no_name():
    """Test: extract_forward_info для MessageOriginHiddenUser без имени"""
    forward = MessageOriginHiddenUser(date=datetime.now(), sender_user_name="")
    msg = AsyncMock()
    msg.forward_origin = forward
    
    result = extract_forward_info(msg)
    
    assert result is not None
    sender_id, sender_name = result
    assert sender_id == 0
    assert sender_name == ""


def test_extract_forward_info_chat_no_title():
    """Test: extract_forward_info для MessageOriginChat без title"""
    sender_chat = Chat(id=-1001234567890, type="channel", title=None)
    forward = MessageOriginChat(date=datetime.now(), sender_chat=sender_chat)
    msg = AsyncMock()
    msg.forward_origin = forward
    
    result = extract_forward_info(msg)
    
    assert result is not None
    sender_id, sender_name = result
    assert sender_id == -1001234567890
    assert sender_name is None


@pytest.mark.asyncio
async def test_message_handler_no_forward(mock_message_no_forward):
    """Test: message_handler для обычного сообщения (без forward_origin)"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_no_forward)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        assert call_args[0][0] == 123456789  # user_id
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.id == "1"
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 123456789
        assert inbox_message.sender_name == "Test User"
        assert inbox_message.content == "Test message"
        assert inbox_message.chat_id == 123456789


@pytest.mark.asyncio
async def test_message_handler_forward_user(mock_message_forward_user):
    """Test: message_handler для MessageOriginUser"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_user)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        assert call_args[0][0] == 123456789  # user_id (forwarder)
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.id == "2"
        assert inbox_message.from_user == 123456789  # forwarder
        assert inbox_message.sender_id == 987654321  # original author
        assert inbox_message.sender_name == "Original Sender"
        assert inbox_message.content == "Forwarded message"
        assert inbox_message.chat_id == 123456789


@pytest.mark.asyncio
async def test_message_handler_forward_hidden_user(mock_message_forward_hidden_user):
    """Test: message_handler для MessageOriginHiddenUser"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_hidden_user)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        assert call_args[0][0] == 123456789
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 0
        assert inbox_message.sender_name == "Hidden User"
        assert inbox_message.content == "Hidden forwarded message"


@pytest.mark.asyncio
async def test_message_handler_forward_chat(mock_message_forward_chat):
    """Test: message_handler для MessageOriginChat"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_chat)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == -1001234567890
        assert inbox_message.sender_name == "News Channel"
        assert inbox_message.content == "Chat forwarded message"


@pytest.mark.asyncio
async def test_message_handler_forward_hidden_no_name(mock_message_forward_hidden_no_name):
    """Test: message_handler для пересылки без sender_name"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        await message_handler(mock_message_forward_hidden_no_name)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 0
        assert inbox_message.sender_name == ""
        assert inbox_message.content == "Forwarded without sender"


@pytest.mark.asyncio
async def test_message_handler_forward_chat_no_title(mock_message_forward_chat_no_title):
    """Test: message_handler для пересылки из чата без sender_title"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        await message_handler(mock_message_forward_chat_no_title)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == -1001234567890
        assert inbox_message.sender_name is None
        assert inbox_message.content == "Forwarded without title"


@pytest.mark.asyncio
async def test_message_handler_forward_caption(mock_message_forward_caption):
    """Test: message_handler для пересылки с caption вместо text"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_caption)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        assert isinstance(inbox_message, InboxMessage)
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 987654321
        assert inbox_message.sender_name == "Photo Sender"
        assert inbox_message.content == "Photo caption"


@pytest.mark.asyncio
async def test_full_cycle_forward_user(mock_message_forward_user):
    """Integration test: full cycle message_handler → FileManager.append_message для MessageOriginUser"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_user)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        user_id = call_args[0][0]
        inbox_message = call_args[0][1]
        
        assert user_id == 123456789
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 987654321
        assert inbox_message.sender_name == "Original Sender"
        
        assert user_id != inbox_message.sender_id


@pytest.mark.asyncio
async def test_full_cycle_forward_chat(mock_message_forward_chat):
    """Integration test: full cycle message_handler → FileManager.append_message для MessageOriginChat"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_forward_chat)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == -1001234567890
        assert inbox_message.sender_name == "News Channel"


@pytest.mark.asyncio
async def test_full_cycle_no_forward(mock_message_no_forward):
    """Integration test: full cycle message_handler → FileManager.append_message для обычного сообщения"""
    with patch('handlers.messages.file_manager') as mock_file_manager:
        
        
        
        await message_handler(mock_message_no_forward)
        
        mock_file_manager.append_message.assert_called_once()
        call_args = mock_file_manager.append_message.call_args
        
        inbox_message = call_args[0][1]
        
        assert inbox_message.from_user == 123456789
        assert inbox_message.sender_id == 123456789
        assert inbox_message.sender_name == "Test User"