from typing import Callable, Optional, Tuple
from aiogram import Router
from aiogram.types import Message
from aiogram.types import ForwardOrigin, ForwardOriginUser, ForwardOriginHiddenUser, ForwardOriginChat

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage


router = Router()
file_manager = FileManager()


def extract_forward_info(message: Message) -> Optional[Tuple[int, Optional[str]]]:
    if not message.forward_origin:
        return None
    
    forward_origin = message.forward_origin
    
    if isinstance(forward_origin, ForwardOriginUser):
        return (forward_origin.sender_id, forward_origin.sender_user.name)
    elif isinstance(forward_origin, ForwardOriginHiddenUser):
        return (forward_origin.sender_id, forward_origin.sender_user.name)
    elif isinstance(forward_origin, ForwardOriginChat):
        return (forward_origin.chat.id, forward_origin.sender_title)
    
    return None


async def message_handler(message: Message) -> None:
    user_id = message.from_user.id
    
    forward_info = extract_forward_info(message)
    
    if forward_info:
        sender_id, sender_name = forward_info
    else:
        sender_id = user_id
        sender_name = message.from_user.full_name if message.from_user else None
    
    content = message.text or str(message.caption)
    
    inbox_message = InboxMessage(
        id=str(message.message_id),
        timestamp=message.date,
        from_user=user_id,
        sender_id=sender_id,
        sender_name=sender_name,
        content=content,
        chat_id=message.chat.id
    )
    
    file_manager.append_message(user_id, inbox_message)