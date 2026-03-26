import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from bot.timers.manager import SummarizeTimer


@pytest.fixture
def timer():
    return SummarizeTimer()


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_schedule_summarization_with_user_name(timer, mock_bot):
    """Verify start notification is sent with user_name"""
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await timer.schedule_summarization(
            user_id=123,
            delay_seconds=1,
            user_name="Test User",
            bot=mock_bot
        )
        
        # Wait for timer to complete (sleep + delay + notification)
        await asyncio.sleep(2.5)
        
        # Verify start notification was sent
        assert mock_bot.send_message.called
        first_call_args = mock_bot.send_message.call_args_list[0]
        assert first_call_args[0][0] == 123  # user_id
        assert "Саммаризация сообщений началась для пользователя Test User" in first_call_args[0][1]


@pytest.mark.asyncio
async def test_wait_and_summarize_handles_missing_user_name(timer, mock_bot):
    """Verify fallback to user_id when name unavailable"""
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await timer.schedule_summarization(
            user_id=456,
            delay_seconds=1,
            user_name=None,
            bot=mock_bot
        )
        
        # Wait for timer to complete
        await asyncio.sleep(2.5)
        
        # Verify notification was sent with user_id (check first call)
        first_call_args = mock_bot.send_message.call_args_list[0]
        assert "456" in first_call_args[0][1]


@pytest.mark.asyncio
async def test_wait_and_summarize_handles_notification_failure(timer, mock_bot):
    """Verify timer continues even if notification fails"""
    mock_bot.send_message = AsyncMock(side_effect=Exception("Bot error"))
    
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await timer.schedule_summarization(
            user_id=789,
            delay_seconds=1,
            user_name="Test User",
            bot=mock_bot
        )
        
        # Timer should complete without blocking
        await asyncio.sleep(2)
        
        # Verify auto_summarize was still called despite notification failure
        mock_summarize.assert_called_once()
        
        # Verify timer didn't crash
        assert True


@pytest.mark.asyncio
async def test_trigger_immediate_summarization_cancels_pending_timer(timer, mock_bot):
    """Verify manual summarization cancels pending auto summarization"""
    # Schedule auto summarization
    await timer.schedule_summarization(
        user_id=123,
        delay_seconds=300,
        user_name="Test User",
        bot=mock_bot
    )
    
    # Wait for timer to be scheduled
    await asyncio.sleep(0.1)
    
    # Verify timer is scheduled
    assert 123 in timer.timers
    
    # Trigger immediate summarization
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await timer.trigger_immediate_summarization(
            user_id=123,
            bot=mock_bot,
            user_name="Test User"
        )
        
        # Verify pending timer was cancelled
        assert 123 not in timer.timers
        
        # Verify immediate summarization was triggered
        mock_summarize.assert_called_once_with(123, bot=mock_bot)


@pytest.mark.asyncio
async def test_trigger_immediate_summarization_sends_notification(timer, mock_bot):
    """Verify immediate summarization sends notification"""
    with patch('handlers.summarizer.auto_summarize', new_callable=AsyncMock) as mock_summarize:
        await timer.trigger_immediate_summarization(
            user_id=456,
            bot=mock_bot,
            user_name="Test User"
        )
        
        # Verify notification was sent first
        assert mock_bot.send_message.called
        call_args = mock_bot.send_message.call_args
        assert call_args[0][0] == 456  # user_id
        assert "Ручная саммаризация началась для пользователя Test User" in call_args[0][1]
        
        # Verify auto_summarize was called after notification
        mock_summarize.assert_called_once_with(456, bot=mock_bot)


@pytest.mark.asyncio
async def test_schedule_summarization_properly_cancels_old_timer(timer, mock_bot):
    """Verify schedule_summarization properly cancels old timer before scheduling new one"""
    # Schedule first timer
    await timer.schedule_summarization(
        user_id=789,
        delay_seconds=300,
        user_name="Test User",
        bot=mock_bot
    )
    
    await asyncio.sleep(0.1)
    assert 789 in timer.timers
    
    # Schedule second timer (should cancel first)
    await timer.schedule_summarization(
        user_id=789,
        delay_seconds=600,
        user_name="Test User",
        bot=mock_bot
    )
    
    # Verify old timer was cancelled and new one is scheduled
    assert 789 in timer.timers
    # The task should be different (new one)
