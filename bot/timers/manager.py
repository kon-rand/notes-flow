import asyncio
from typing import Dict


class SummarizeTimer:
    def __init__(self):
        self.timers: Dict[int, asyncio.Task] = {}

    async def schedule_summarization(self, user_id: int, delay_seconds: int):
        """Запланировать саммаризацию с задержкой"""
        if user_id in self.timers:
            old_task = self.timers[user_id]
            old_task.cancel()
            await asyncio.sleep(0.01)

        task = asyncio.create_task(self._wait_and_summarize(user_id, delay_seconds))
        self.timers[user_id] = task

    async def reset(self, user_id: int):
        """Сбросить таймер при новом сообщении"""
        if user_id in self.timers:
            task = self.timers[user_id]
            task.cancel()
            del self.timers[user_id]
            await asyncio.sleep(0.01)

    async def _wait_and_summarize(self, user_id: int, delay: int):
        """Асинхронный таймер с задержкой"""
        await asyncio.sleep(delay)

        from handlers.summarizer import auto_summarize
        await auto_summarize(user_id)