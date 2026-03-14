import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import settings
from handlers.commands import router as commands_router
from handlers.messages import router as messages_router
from handlers.summarizer import router as summarizer_router
from bot.healthcheck import healthcheck as healthcheck_func, ping as ping_func
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def healthcheck_handler() -> JSONResponse:
    """Проверка здоровья приложения и подключения к AI API"""
    result = await healthcheck_func()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


async def ping_handler() -> JSONResponse:
    """Проверка подключения к AI модели"""
    result = await ping_func()
    status_code = 200 if result["status"] == "ok" else 503
    return JSONResponse(content=result, status_code=status_code)


async def run_bot():
    """Запуск Telegram бота"""
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
        BotCommand(command="complete", description="просмотр архивов"),
        BotCommand(command="archive", description="архивация задач"),
    ]
    await bot.set_my_commands(commands)

    dp.include_router(commands_router)
    dp.include_router(messages_router)
    dp.include_router(summarizer_router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

    await bot.close()


async def run_server():
    """Запуск FastAPI сервера"""
    from fastapi import FastAPI

    app = FastAPI(title="Notes Flow API")
    app.add_api_route("/healthcheck", healthcheck_handler, methods=["GET"])
    app.add_api_route("/ping", ping_handler, methods=["GET"])

    import uvicorn
    logging.info("Starting HTTP server on 0.0.0.0:8081...")
    config = uvicorn.Config(app, host="0.0.0.0", port=8081, loop="uvloop")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.info("Starting Notes Flow application...")
    
    bot_task = asyncio.create_task(run_bot())
    server_task = asyncio.create_task(run_server())

    await asyncio.gather(bot_task, server_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application stopped")