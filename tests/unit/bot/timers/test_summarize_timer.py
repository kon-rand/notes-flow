import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from bot.timers.manager import SummarizeTimer


@pytest.fixture
def timer():
    return SummarizeTimer()


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
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
        
        # Wait for timer to complete
        await asyncio.sleep(2)
        
        # Verify start notification was sent (check first call only)
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
        
        await asyncio.sleep(2)
        
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
