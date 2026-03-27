from typing import Optional, Tuple
from aiogram import F, Router
from aiogram.types import Message
from aiogram.types.message_origin_user import MessageOriginUser
from aiogram.types.message_origin_hidden_user import MessageOriginHiddenUser
from aiogram.types.message_origin_chat import MessageOriginChat
import os
import time

from bot.db.file_manager import FileManager
from bot.db.models import InboxMessage
from bot.timers.manager import summarizer_timer


router = Router()
file_manager = FileManager()


async def no_command(message: Message) -> bool:
    """Filter to exclude all commands from inbox handler"""
    if message.text is None:
        return False
    return not message.text.startswith('/')


def extract_forward_info(message: Message) -> Optional[Tuple[int, Optional[str]]]:
    if not message.forward_origin:
        return None
    
    forward_origin = message.forward_origin
    
    if isinstance(forward_origin, MessageOriginUser):
        sender_user = forward_origin.sender_user
        sender_name = f"{sender_user.first_name} {sender_user.last_name}" if sender_user.last_name else sender_user.first_name
        return (sender_user.id, sender_name)
    elif isinstance(forward_origin, MessageOriginHiddenUser):
        return (0, forward_origin.sender_user_name)
    elif isinstance(forward_origin, MessageOriginChat):
        sender_chat = forward_origin.sender_chat
        return (sender_chat.id, sender_chat.title)
    
    return None


@router.message(no_command)
async def message_handler(message: Message) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    
    forward_info = extract_forward_info(message)
    
    if forward_info:
        sender_id, sender_name = forward_info
    else:
        sender_id = user_id
        sender_name = message.from_user.full_name if message.from_user else None
    
    content = message.text or str(message.caption)
    
    print(f"DEBUG: User {user_id}, Forward: {forward_info}, Sender: {sender_name}, Content: {content[:50]}")
    
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
    print(f"DEBUG: Saved message {message.message_id} for user {user_id}")
    
    user_name = message.from_user.full_name if message.from_user else None
    await summarizer_timer.schedule_summarization(
        user_id=user_id,
        user_name=user_name,
        bot=message.bot
    )


@router.message(F.document)
async def restore_document_handler(message: Message):
    """Обработка загрузки ZIP файла для восстановления"""
    if message.from_user is None:
        return
    
    user_id = message.from_user.id
    
    # Проверяем, что это ZIP файл
    if not message.document.file_name.endswith('.zip'):
        await message.answer("Пожалуйста, загрузите ZIP-файл")
        return
    
    try:
        bot = message.bot
        file = await bot.get_file(message.document.file_id)
        file_path = f"/tmp/restore_{user_id}_{int(time.time())}.zip"
        await bot.download_file(file.file_path, file_path)
        
        file_manager = FileManager()
        result = file_manager.restore_from_backup(user_id, file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result['success']:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result.get('error', 'Ошибка при восстановлении')}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")