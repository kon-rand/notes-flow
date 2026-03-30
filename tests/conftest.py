import os
import shutil
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def setup_test_isolation(tmp_path):
    """Set up test isolation before each test"""
    # Save current working directory
    original_cwd = os.getcwd()
    
    # Change to tmp_path to ensure all file operations are isolated
    os.chdir(str(tmp_path))
    
    # Clean up any existing data directory
    data_dir = Path("data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
    
    # Clean up user_settings.json
    settings_file = Path("data/user_settings.json")
    if settings_file.exists():
        settings_file.unlink()
    
    yield
    
    # Restore original working directory
    os.chdir(original_cwd)
    
    # Clean up data directory
    if data_dir.exists():
        shutil.rmtree(data_dir)
    
    # Clean up user_settings.json
    if settings_file.exists():
        settings_file.unlink()
