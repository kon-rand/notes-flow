import asyncio
import sys
sys.path.insert(0, '/home/kuzya/projects/notes-flow')

from bot.timers.manager import SummarizeTimer


async def test_creates_task():
    """Тест: создание asyncio.Task и добавление в словарь"""
    timer = SummarizeTimer()
    await timer.schedule_summarization(user_id=123, delay_seconds=300)
    
    assert 123 in timer.timers
    assert isinstance(timer.timers[123], asyncio.Task)
    print("✓ test_creates_task passed")


async def test_cancels_previous():
    """Тест: отмена предыдущего таймера при scheduling нового"""
    timer = SummarizeTimer()
    
    old_task = asyncio.create_task(asyncio.sleep(1000))
    timer.timers[456] = old_task
    
    await timer.schedule_summarization(user_id=456, delay_seconds=600)
    
    assert old_task.cancelled()
    print("✓ test_cancels_previous passed")


async def test_reset():
    """Тест: сброс таймера - отмена task и удаление из словаря"""
    timer = SummarizeTimer()
    
    task = asyncio.create_task(asyncio.sleep(1000))
    timer.timers[789] = task
    
    await timer.reset(789)
    await asyncio.sleep(0.01)
    
    assert task.cancelled()
    assert 789 not in timer.timers
    print("✓ test_reset passed")


async def test_multiple_users():
    """Тест: изоляция пользователей"""
    timer = SummarizeTimer()
    
    await timer.schedule_summarization(user_id=100, delay_seconds=300)
    await timer.schedule_summarization(user_id=200, delay_seconds=600)
    await timer.schedule_summarization(user_id=300, delay_seconds=900)
    
    assert len(timer.timers) == 3
    
    await timer.reset(200)
    
    assert len(timer.timers) == 2
    assert 100 in timer.timers
    assert 200 not in timer.timers
    assert 300 in timer.timers
    print("✓ test_multiple_users passed")


async def test_reset_nonexistent():
    """Тест: отсутствие ошибки при сбросе несуществующего пользователя"""
    timer = SummarizeTimer()
    
    await timer.reset(999)
    
    assert len(timer.timers) == 0
    print("✓ test_reset_nonexistent passed")


async def test_message_flow():
    """Тест: обработка сообщений → reset таймера → schedule нового"""
    timer = SummarizeTimer()
    
    await timer.schedule_summarization(user_id=100, delay_seconds=300)
    assert len(timer.timers) == 1
    
    await timer.reset(100)
    assert len(timer.timers) == 0
    
    await timer.schedule_summarization(user_id=100, delay_seconds=600)
    assert len(timer.timers) == 1
    print("✓ test_message_flow passed")


async def main():
    print("Running SummarizeTimer tests...\n")
    
    await test_creates_task()
    await test_cancels_previous()
    await test_reset()
    await test_multiple_users()
    await test_reset_nonexistent()
    await test_message_flow()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())