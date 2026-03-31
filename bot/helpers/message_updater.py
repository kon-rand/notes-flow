"""Helper functions for updating bot messages"""
import logging
from aiogram.types import Message

from bot.config.user_settings import user_settings

logger = logging.getLogger(__name__)


async def update_or_create_task_message(message: Message, text: str) -> int:
    """
    Обновить существующее сообщение /tasks или создать новое.
    
    Args:
        message: Исходное сообщение от пользователя
        text: Текст для отображения
        
    Returns:
        ID отправленного/отредактированного сообщения
    """
    user_id = message.from_user.id if message.from_user else message.chat.id
    
    # Получаем сохранённый message_id
    settings = user_settings.get_counters(user_id)
    saved_message_id = settings.tasks_message_id
    
    try:
        if saved_message_id is not None:
            # Пытаемся отредактировать существующее сообщение
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=saved_message_id,
                    text=text
                )
                logger.debug(f"Edited existing /tasks message {saved_message_id} for user {user_id}")
                return saved_message_id
            except Exception as e:
                # Редактирование не удалось (старое сообщение, удалено и т.д.)
                logger.warning(f"Failed to edit message {saved_message_id}: {e}. Sending new message.")
                # Продолжаем к отправке нового сообщения
        else:
            logger.debug(f"No saved message_id for user {user_id}. Sending new message.")
        
        # Отправляем новое сообщение
        response = await message.answer(text)
        
        # Сохраняем message_id нового сообщения
        if response and response.message_id:
            user_settings.update_tasks_message_id(user_id, response.message_id)
            logger.debug(f"Saved tasks_message_id {response.message_id} for user {user_id}")
        
        return response.message_id if response else 0
        
    except Exception as e:
        logger.error(f"Error updating /tasks message for user {user_id}: {e}")
        # В случае ошибки просто отправляем сообщение без сохранения ID
        await message.answer(text)
        return 0


async def update_or_create_archive_message(message: Message, text: str) -> int:
    """
    Обновить существующее сообщение /archive или создать новое.
    
    Args:
        message: Исходное сообщение от пользователя
        text: Текст для отображения
        
    Returns:
        ID отправленного/отредактированного сообщения
    """
    user_id = message.from_user.id if message.from_user else message.chat.id
    
    # Получаем сохранённый message_id
    settings = user_settings.get_counters(user_id)
    saved_message_id = settings.archive_message_id
    
    try:
        if saved_message_id is not None:
            # Пытаемся отредактировать существующее сообщение
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=saved_message_id,
                    text=text
                )
                logger.debug(f"Edited existing /archive message {saved_message_id} for user {user_id}")
                return saved_message_id
            except Exception as e:
                # Редактирование не удалось
                logger.warning(f"Failed to edit message {saved_message_id}: {e}. Sending new message.")
                # Продолжаем к отправке нового сообщения
        else:
            logger.debug(f"No saved message_id for user {user_id}. Sending new message.")
        
        # Отправляем новое сообщение
        response = await message.answer(text)
        
        # Сохраняем message_id нового сообщения
        if response and response.message_id:
            user_settings.update_archive_message_id(user_id, response.message_id)
            logger.debug(f"Saved archive_message_id {response.message_id} for user {user_id}")
        
        return response.message_id if response else 0
        
    except Exception as e:
        logger.error(f"Error updating /archive message for user {user_id}: {e}")
        # В случае ошибки просто отправляем сообщение без сохранения ID
        await message.answer(text)
        return 0
