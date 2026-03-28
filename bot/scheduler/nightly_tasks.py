"""
Планировщик ночных задач.

Запускает архивацию и бэкапы по расписанию.
"""

import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.db.file_manager import FileManager
from bot.scheduler.backup_scheduler import BackupScheduler, backup_scheduler

logger = logging.getLogger(__name__)

# Инициализация планировщика
scheduler = AsyncIOScheduler()


async def nightly_archive(user_id: int, bot: Bot) -> None:
    """Ночная архивация и создание бэкапа"""
    try:
        logger.info(f"🌙 Запуск ночной архивации для пользователя {user_id}")
        
        file_manager = FileManager()
        today = datetime.now()
        
        # Архивируем выполненные задачи
        archived_tasks = file_manager.archive_completed_tasks(user_id, today)
        
        if archived_tasks:
            logger.info(f"✅ Архивировано {len(archived_tasks)} задач за {today.strftime('%Y-%m-%d')}")
            
            # Запускаем бэкап ТОЛЬКО после ночной архивации
            if backup_scheduler:
                logger.info(f"📦 Планирование бэкапа после ночной архивации для пользователя {user_id}")
                await backup_scheduler.schedule_backup(user_id)
        else:
            logger.info(f"ℹ️ Нет задач для архивации у пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка ночной архивации для пользователя {user_id}: {e}")


def setup_nightly_tasks(bot: Bot) -> None:
    """Настроить ночные задачи"""
    # Архивация и бэкап каждый день в 02:00
    scheduler.add_job(
        nightly_archive,
        trigger=CronTrigger(hour=2, minute=0),
        id='nightly_archive',
        replace_existing=True,
        args=[bot]  # Передаем бота в функцию
    )
    
    logger.info("✅ Ночная архивация настроена на 02:00")


def start_scheduler() -> None:
    """Запустить планировщик"""
    scheduler.start()
    logger.info("🚀 Планировщик ночных задач запущен")


def shutdown_scheduler() -> None:
    """Остановить планировщик"""
    scheduler.shutdown()
    logger.info("🛑 Планировщик ночных задач остановлен")
