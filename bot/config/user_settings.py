"""Персональные настройки пользователей"""
import json
import os
from typing import Dict

SETTINGS_FILE = "data/user_settings.json"


class UserSettings:
    def __init__(self):
        self._settings: Dict[int, int] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self._settings = {int(k): v for k, v in json.load(f).items()}
    
    def _save(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self._settings, f)
    
    def set_delay(self, user_id: int, delay_seconds: int):
        """Установить задержку для конкретного пользователя"""
        self._settings[user_id] = delay_seconds
        self._save()
    
    def get_user_delay(self, user_id: int) -> int:
        """Получить задержку пользователя или дефолтную"""
        from bot.config import settings
        return self._settings.get(user_id, settings.DEFAULT_SUMMARIZE_DELAY)


user_settings = UserSettings()