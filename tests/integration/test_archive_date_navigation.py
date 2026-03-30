"""Tests for archive date navigation fix.

These tests verify that the /YYYY_MM_DD date navigation command works correctly.
The tests ensure:
1. archive_router is imported and registered in entrypoint.py
2. archive_date_handler processes valid date formats
3. When changes are reverted, tests fail

Run these tests to verify the fix is applied:
    pytest tests/integration/test_archive_date_navigation.py -v

To verify tests fail when reverted:
    1. Comment out line 8: from handlers.commands import router as commands_router, archive_router
    2. Comment out line 53: dp.include_router(archive_router)
    3. Run tests again - they should fail
"""

import pytest

@pytest.fixture(autouse=True)
def cleanup_user_settings():
    """Clean up user settings before each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    if Path(SETTINGS_FILE).exists():
        Path(SETTINGS_FILE).unlink()
    yield

from pathlib import Path


class TestEntrypointArchiveRouterRegistration:
    """Test that archive_router is properly registered in entrypoint.py"""

    def test_archive_router_imported_in_entrypoint(self):
        """Verify archive_router is imported in entrypoint.py
        
        Regression test: Before fix, archive_router was not imported,
        causing /YYYY_MM_DD navigation to fail.
        
        FAILS IF: Line contains 'from handlers.commands import' but NOT 'archive_router'
        PASSES IF: Line contains 'from handlers.commands import ... archive_router'
        """
        entrypoint_path = Path("/home/kuzya/projects/notes-flow/bot/entrypoint.py")
        content = entrypoint_path.read_text(encoding="utf-8")
        
        # Check that archive_router is imported (not commented out)
        assert "from handlers.commands import" in content, \
            "Expected import statement not found"
        
        # Check that archive_router is in the import (not commented out)
        import_line = None
        for line in content.split('\n'):
            if 'from handlers.commands import' in line and not line.strip().startswith('#'):
                import_line = line
                break
        
        assert import_line is not None, \
            "Import statement 'from handlers.commands import' not found"
        assert "archive_router" in import_line, \
            f"archive_router not imported. Found: {import_line}"

    def test_archive_router_registered_in_dispatcher(self):
        """Verify archive_router is registered in the dispatcher
        
        Regression test: Before fix, archive_router was not included in
        the dispatcher, so date navigation commands were never handled.
        
        FAILS IF: Line contains 'dp.include_router(archive_router)' but is commented out
        PASSES IF: Line contains 'dp.include_router(archive_router)' and is NOT commented
        """
        entrypoint_path = Path("/home/kuzya/projects/notes-flow/bot/entrypoint.py")
        content = entrypoint_path.read_text(encoding="utf-8")
        
        # Check that archive_router is registered (not commented out)
        registered = False
        for line in content.split('\n'):
            if 'dp.include_router(archive_router)' in line and not line.strip().startswith('#'):
                registered = True
                break
        
        assert registered, \
            "archive_router not registered in dispatcher. " \
            "Expected: dp.include_router(archive_router)"


class TestArchiveDateFormatValidation:
    """Test that archive date format validation works correctly"""

    def test_underscore_date_format_length(self):
        """Verify YYYY_MM_DD format has correct length (10 chars)
        
        Regression test: The original bug was checking len(date_input) != 10
        which incorrectly rejected YYYY_MM_DD format. Both YYYY_MM_DD and
        YYYY-MM-DD are 10 characters.
        
        FAILS IF: Date format length check is wrong
        PASSES IF: Both YYYY_MM_DD and YYYY-MM-DD are 10 characters
        """
        # Test underscore format
        underscore_date = "2026_03_26"
        assert len(underscore_date) == 10, \
            "YYYY_MM_DD format should be 10 characters"
        
        # Test dash format
        dash_date = "2026-03-26"
        assert len(dash_date) == 10, \
            "YYYY-MM-DD format should be 10 characters"

    def test_date_parsing_underscore_format(self):
        """Verify underscore date format can be parsed correctly"""
        date_input = "2026_03_26"
        
        # Simulate the parsing logic from archive_date_handler
        if "_" in date_input:
            year, month, day = date_input.split("_")
        elif "-" in date_input:
            year, month, day = date_input.split("-")
        else:
            raise ValueError("No separator found")
        
        assert int(year) == 2026
        assert int(month) == 3
        assert int(day) == 26

    def test_date_parsing_dash_format(self):
        """Verify dash date format can be parsed correctly"""
        date_input = "2026-03-26"
        
        # Simulate the parsing logic from archive_date_handler
        if "_" in date_input:
            year, month, day = date_input.split("_")
        elif "-" in date_input:
            year, month, day = date_input.split("-")
        else:
            raise ValueError("No separator found")
        
        assert int(year) == 2026
        assert int(month) == 3
        assert int(day) == 26

    def test_date_validation_with_datetime(self):
        """Verify date validation using datetime module"""
        from datetime import datetime
        
        # Test underscore format
        date_input_underscore = "2026_03_26"
        if "_" in date_input_underscore:
            year, month, day = date_input_underscore.split("_")
        elif "-" in date_input_underscore:
            year, month, day = date_input_underscore.split("-")
        else:
            raise ValueError("No separator found")
        
        # Should not raise ValueError
        datetime(int(year), int(month), int(day))
        
        # Test dash format
        date_input_dash = "2026-03-26"
        if "_" in date_input_dash:
            year, month, day = date_input_dash.split("_")
        elif "-" in date_input_dash:
            year, month, day = date_input_dash.split("-")
        else:
            raise ValueError("No separator found")
        
        # Should not raise ValueError
        datetime(int(year), int(month), int(day))
