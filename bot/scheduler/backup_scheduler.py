import hashlib
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot

from bot.db.backup_state import BackupStateManager
from bot.db.file_manager import FileManager
from bot.scheduler.notifications import NotificationSender
from utils.backup_validator import has_changes

logger = logging.getLogger(__name__)


class BackupScheduler:
    def __init__(self, bot: Bot, data_dir: str = "data"):
        self.bot = bot
        self.data_dir = Path(data_dir)
        self.file_manager = FileManager(data_dir)
        self.notification_sender = NotificationSender(bot)
        self.state_manager = BackupStateManager(f"{data_dir}/backup_state.json")
        self._tasks: dict[int, asyncio.Task] = {}
    
    async def schedule_backup(self, user_id: int) -> None:
        logger.info(f"Scheduled backup for user {user_id}")
        if user_id in self._tasks:
            self._tasks[user_id].cancel()
        self._tasks[user_id] = asyncio.create_task(self._check_and_create_backup(user_id))
    
    async def _check_and_create_backup(self, user_id: int) -> None:
        try:
            await self._check_and_create_backup_for_user(user_id)
        except Exception as e:
            logger.error(f"Error in backup scheduler for user {user_id}: {e}")
        finally:
            self._tasks.pop(user_id, None)
    
    async def _check_and_create_backup_for_user(self, user_id: int) -> None:
        last_state = self.state_manager.get_last_state(user_id)
        if last_state and last_state.last_backup_timestamp:
            if not has_changes(user_id, last_state.last_backup_timestamp, self.data_dir):
                logger.info(f"No changes for user {user_id} since last backup")
                await self.notification_sender.send_no_changes_notification(user_id)
                return
        
        logger.info(f"Creating backup for user {user_id}")
        backup_result = await self._create_backup(user_id)
        if backup_result:
            await self.notification_sender.send_backup(
                user_id, backup_result, "backup.zip"
            )
            last_state = self.state_manager.get_last_state(user_id)
            if not last_state:
                last_state = datetime.now()
            else:
                last_state = datetime.now()
            self.state_manager.save_state(user_id, last_state, str(hashlib.md5(backup_result).hexdigest()))
        else:
            await self.notification_sender.send_error_notification(
                user_id, "Failed to create backup"
            )
    
    async def _create_backup(self, user_id: int) -> Optional[bytes]:
        try:
            backup = self.file_manager.create_backup(user_id)
            if backup:
                return backup.getvalue()
            return None
        except Exception as e:
            logger.error(f"Error creating backup for user {user_id}: {e}")
            return None
