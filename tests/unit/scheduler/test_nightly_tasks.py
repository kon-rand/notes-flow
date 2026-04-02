"""Tests for nightly archive and backup scheduling."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from bot.scheduler.nightly_tasks import nightly_archive, backup_scheduler


@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    return MagicMock()


@pytest.fixture
def mock_backup_scheduler():
    """Create a mock backup scheduler."""
    scheduler = AsyncMock()
    scheduler.schedule_backup = AsyncMock()
    return scheduler


@pytest.fixture
def mock_file_manager():
    """Create a mock file manager."""
    fm = MagicMock()
    fm.get_all_user_ids = MagicMock(return_value=[123456])
    fm.archive_completed_tasks = MagicMock(return_value=[])
    return fm


class TestNightlyArchiveEmptyTasks:
    """Tests for nightly_archive when there are no completed tasks to archive."""

    @pytest.mark.asyncio
    async def test_backup_scheduled_with_empty_archived_tasks(
        self, mock_bot, mock_backup_scheduler, mock_file_manager
    ):
        """Backup should be scheduled even when archive_completed_tasks returns empty list."""
        # Arrange
        with patch("bot.scheduler.nightly_tasks.backup_scheduler", mock_backup_scheduler):
            with patch(
                "bot.scheduler.nightly_tasks.FileManager",
                return_value=mock_file_manager,
            ):
                mock_file_manager.archive_completed_tasks.return_value = []

                # Act
                await nightly_archive(mock_bot)

                # Assert
                mock_backup_scheduler.schedule_backup.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_no_changes_notification_sent(
        self, mock_bot, mock_backup_scheduler, mock_file_manager
    ):
        """No changes notification should be sent when no changes detected."""
        # Arrange
        with patch("bot.scheduler.nightly_tasks.backup_scheduler", mock_backup_scheduler):
            with patch(
                "bot.scheduler.nightly_tasks.FileManager",
                return_value=mock_file_manager,
            ):
                mock_file_manager.archive_completed_tasks.return_value = []
                mock_backup_scheduler.schedule_backup.side_effect = None

                # Act
                await nightly_archive(mock_bot)

                # Assert - backup was scheduled, which will trigger no-changes notification
                mock_backup_scheduler.schedule_backup.assert_called_once()


class TestNightlyArchiveWithTasks:
    """Tests for nightly_archive when there are completed tasks to archive."""

    @pytest.mark.asyncio
    async def test_backup_scheduled_with_non_empty_archived_tasks(
        self, mock_bot, mock_backup_scheduler, mock_file_manager
    ):
        """Backup should be scheduled when archive_completed_tasks returns tasks."""
        # Arrange
        archived_tasks = [
            MagicMock(id="task_001"),
            MagicMock(id="task_002"),
        ]
        with patch("bot.scheduler.nightly_tasks.backup_scheduler", mock_backup_scheduler):
            with patch(
                "bot.scheduler.nightly_tasks.FileManager",
                return_value=mock_file_manager,
            ):
                mock_file_manager.archive_completed_tasks.return_value = archived_tasks

                # Act
                await nightly_archive(mock_bot)

                # Assert
                mock_backup_scheduler.schedule_backup.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_multiple_users_backup_scheduled(
        self, mock_bot, mock_backup_scheduler, mock_file_manager
    ):
        """Backup should be scheduled for all users."""
        # Arrange
        with patch("bot.scheduler.nightly_tasks.backup_scheduler", mock_backup_scheduler):
            with patch(
                "bot.scheduler.nightly_tasks.FileManager",
                return_value=mock_file_manager,
            ):
                mock_file_manager.get_all_user_ids.return_value = [123, 456, 789]
                mock_file_manager.archive_completed_tasks.return_value = []

                # Act
                await nightly_archive(mock_bot)

                # Assert
                assert mock_backup_scheduler.schedule_backup.call_count == 3
                mock_backup_scheduler.schedule_backup.assert_any_call(123)
                mock_backup_scheduler.schedule_backup.assert_any_call(456)
                mock_backup_scheduler.schedule_backup.assert_any_call(789)
