import asyncio
from typing import Dict, Optional

from aiogram import Bot

from ..config.user_settings import user_settings


class SummarizeTimer:
    def __init__(self) -> None:
        self.timers: Dict[int, asyncio.Task] = {}

    async def schedule_summarization(
        self, 
        user_id: int, 
        delay_seconds: Optional[int] = None,
        user_name: Optional[str] = None,
        bot: Optional[Bot] = None
    ) -> None:
        """Запланировать саммаризацию с задержкой"""
        if delay_seconds is None:
            delay_seconds = user_settings.get_user_delay(user_id)

        if user_id in self.timers:
            old_task = self.timers[user_id]
            old_task.cancel()
            await asyncio.sleep(0.01)

        task = asyncio.create_task(
            self._wait_and_summarize(user_id, delay_seconds, user_name, bot)
        )
        self.timers[user_id] = task

    async def reset(self, user_id: int) -> None:
        """Сбросить таймер при новом сообщении"""
        if user_id in self.timers:
            task = self.timers[user_id]
            task.cancel()
            del self.timers[user_id]
            await asyncio.sleep(0.01)

    async def _wait_and_summarize(
        self, 
        user_id: int, 
        delay: int, 
        user_name: Optional[str] = None,
        bot: Optional[Bot] = None
    ) -> None:
        """Асинхронный таймер с задержкой"""
        await asyncio.sleep(delay)
        
        if bot:
            display_name = user_name or str(user_id)
            try:
                await bot.send_message(
                    user_id,
                    f"🔄 Саммаризация сообщений началась для пользователя {display_name}"
                )
            except Exception:
                pass

        from handlers.summarizer import auto_summarize
        await auto_summarize(user_id, bot=bot)


summarizer_timer = SummarizeTimer()