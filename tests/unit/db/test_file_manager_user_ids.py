

"""Тесты для метода get_all_user_ids в FileManager"""
import pytest

@pytest.fixture(autouse=True)
def cleanup_user_settings(tmp_path):
    """Clean up user settings before and after each test to ensure isolation"""
    from bot.config.user_settings import SETTINGS_FILE
    settings_path = tmp_path / SETTINGS_FILE
    if settings_path.exists():
        settings_path.unlink()
    yield
    if settings_path.exists():
        settings_path.unlink()

from pathlib import Path
from bot.db.file_manager import FileManager


@pytest.fixture
def temp_data_dir(tmp_path):
    """Создать временную директорию для тестов"""
    # Создаём несколько user директорий
    (tmp_path / "123").mkdir()
    (tmp_path / "456").mkdir()
    (tmp_path / "789").mkdir()
    # Создаём файл который должен быть пропущен
    (tmp_path / "user_settings.json").write_text("{}")
    return tmp_path


@pytest.fixture
def file_manager(temp_data_dir):
    """Создать FileManager с временной директорией"""
    return FileManager(data_dir=str(temp_data_dir))


def test_get_all_user_ids(file_manager, temp_data_dir):
    """Проверить что get_all_user_ids возвращает только директории с цифрами"""
    user_ids = file_manager.get_all_user_ids()
    
    # Должны быть только user_id (123, 456, 789)
    assert set(user_ids) == {123, 456, 789}
    assert len(user_ids) == 3


def test_get_all_user_ids_empty_dir():
    """Проверить что get_all_user_ids возвращает пустой список для пустой директории"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        fm = FileManager(data_dir=tmp_dir)
        user_ids = fm.get_all_user_ids()
        assert user_ids == []


def test_get_all_user_ids_no_dir():
    """Проверить что get_all_user_ids не падает если директория не существует"""
    fm = FileManager(data_dir="/nonexistent/path/12345")
    user_ids = fm.get_all_user_ids()
    assert user_ids == []


def test_get_all_user_ids_mixed_content(temp_data_dir):
    """Проверить что get_all_user_ids игнорирует нецифровые директории"""
    # Добавляем нецифровую директорию
    (temp_data_dir / "archive_backup").mkdir()
    (temp_data_dir / "logs").mkdir()
    
    fm = FileManager(data_dir=str(temp_data_dir))
    user_ids = fm.get_all_user_ids()
    
    # Должны быть только цифровые user_id
    assert set(user_ids) == {123, 456, 789}
    assert len(user_ids) == 3
