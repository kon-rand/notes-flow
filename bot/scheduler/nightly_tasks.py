"""
Планировщик ночных задач.

Запускает архивацию и бэкапы по расписанию.
"""

import logging
from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.db.file_manager import FileManager
import bot.scheduler.backup_scheduler as backup_scheduler_module

logger = logging.getLogger(__name__)

# Инициализация планировщика
scheduler = AsyncIOScheduler()


async def nightly_archive(bot: Bot) -> None:
    """Ночная архивация и создание бэкапа для всех пользователей"""
    try:
        logger.info(f"🌙 Запуск ночной архивации для всех пользователей")
        
        file_manager = FileManager()
        today = datetime.now()
        
        # Получаем список всех пользователей
        user_ids = file_manager.get_all_user_ids()
        logger.info(f"📊 Найдено пользователей: {len(user_ids)}")
        
        for user_id in user_ids:
            try:
                logger.info(f"🌙 Обработка пользователя {user_id}")
                
                # Архивируем выполненные задачи
                archived_tasks = file_manager.archive_completed_tasks(user_id, today)
                
                if archived_tasks:
                    logger.info(f"✅ Архивировано {len(archived_tasks)} задач за {today.strftime('%Y-%m-%d')}")
                else:
                    logger.info(f"ℹ️ Нет задач для архивации у пользователя {user_id}")
                
                # Запускаем бэкап всегда после ночной архивации
                if backup_scheduler_module.backup_scheduler:
                    logger.info(f"📦 Планирование бэкапа для пользователя {user_id}")
                    await backup_scheduler_module.backup_scheduler.schedule_backup(user_id)
            except Exception as e:
                logger.error(f"❌ Ошибка обработки пользователя {user_id}: {e}")
                continue
            
    except Exception as e:
        logger.error(f"❌ Ошибка ночной архивации: {e}")


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
    logger.info(f"   Будет обрабатывать всех пользователей из data/")


def start_scheduler() -> None:
    """Запустить планировщик"""
    scheduler.start()
    logger.info("🚀 Планировщик ночных задач запущен")


def shutdown_scheduler() -> None:
    """Остановить планировщик"""
    scheduler.shutdown()
    logger.info("🛑 Планировщик ночных задач остановлен")
