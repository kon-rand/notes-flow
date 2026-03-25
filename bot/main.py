import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import settings
from handlers.commands import router as commands_router, archive_router
from handlers.messages import router as messages_router
from handlers.summarizer import router as summarizer_router

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    commands = [
        BotCommand(command="start", description="показать статистику"),
        BotCommand(command="help", description="список команд"),
        BotCommand(command="summarize", description="ручная саммаризация"),
        BotCommand(command="settings", description="настройка задержки"),
        BotCommand(command="inbox", description="просмотр инбокса"),
        BotCommand(command="tasks", description="список задач"),
        BotCommand(command="notes", description="список заметок"),
        BotCommand(command="clear", description="очистка инбокса"),
        BotCommand(command="archived", description="просмотр архивов"),
        BotCommand(command="archive", description="архивация задач"),
    ]
    await bot.set_my_commands(commands)

    dp.include_router(summarizer_router)
    dp.include_router(commands_router)
    dp.include_router(archive_router)
    dp.include_router(messages_router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

    await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")