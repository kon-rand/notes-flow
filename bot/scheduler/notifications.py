"""
Модуль для отправки уведомлений пользователям.

Отправляет текстовые сообщения и файлы через Telegram Bot API.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)


class NotificationSender:
    """Отправка уведомлений пользователям через Telegram."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_notification(
        self,
        user_id: int,
        message: str,
        file_path: Optional[str] = None
    ) -> bool:
        """
        Отправить уведомление пользователю.
        
        Args:
            user_id: ID пользователя Telegram
            message: Текст сообщения
            file_path: Путь к файлу (опционально)
            
        Returns:
            True если успешно отправлено, False если ошибка
        """
        try:
            if file_path:
                # Отправить с файлом
                file = Path(file_path)
                if not file.exists():
                    logger.error(f"File not found: {file_path}")
                    return False
                
                await self.bot.send_document(
                    chat_id=user_id,
                    document=FSInputFile(str(file)),
                    caption=message,
                    filename=file.name
                )
                logger.info(f"Backup sent to user {user_id} with file: {file.name}")
            else:
                # Отправить только текст
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                logger.info(f"Notification sent to user {user_id}: {message[:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
    async def send_backup(
        self,
        user_id: int,
        backup_content: bytes,
        filename: str = "backup.zip"
    ) -> bool:
        """
        Отправить бэкап пользователю.
        
        Args:
            user_id: ID пользователя Telegram
            backup_content: Контент бэкапа в виде байтов
            filename: Имя файла бэкапа
            
        Returns:
            True если успешно отправлено, False если ошибка
        """
        try:
            # Отправить как документ
            await self.bot.send_document(
                chat_id=user_id,
                document=backup_content,
                filename=filename,
                caption="📦 Ежедневный бэкап создан"
            )
            logger.info(f"Backup sent to user {user_id}: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send backup to user {user_id}: {e}")
            return False
    
    async def send_no_changes_notification(self, user_id: int) -> bool:
        """
        Отправить уведомление об отсутствии изменений.
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            True если успешно отправлено, False если ошибка
        """
        message = "ℹ️ Данные не изменились за последние 24 часа\n\nБэкап не создан."
        return await self.send_notification(user_id, message)
    
    async def send_error_notification(
        self,
        user_id: int,
        error_message: str
    ) -> bool:
        """
        Отправить уведомление об ошибке.
        
        Args:
            user_id: ID пользователя Telegram
            error_message: Сообщение об ошибке
            
        Returns:
            True если успешно отправлено, False если ошибка
        """
        message = f"❌ Ошибка при создании бэкапа:\n{error_message}"
        return await self.send_notification(user_id, message)
