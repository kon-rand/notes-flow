"""Персональные настройки пользователей"""
import json
import os
from typing import Dict, Optional

from bot.db.models import UserSettings as UserSettingsModel

SETTINGS_FILE = "data/user_settings.json"


class UserSettings:
    def __init__(self):
        self._settings: Dict[int, UserSettingsModel] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                # Convert dict to UserSettingsModel
                self._settings = {}
                for uid, data_dict in data.items():
                    self._settings[int(uid)] = UserSettingsModel(**data_dict)
        else:
            self._settings = {}
    
    def _save(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        # Convert UserSettingsModel to dict for JSON serialization
        data = {
            str(uid): {
                "delay": settings.delay,
                "last_task_id": settings.last_task_id,
                "last_note_id": settings.last_note_id,
                "last_message_id": settings.last_message_id,
                "tasks_message_id": settings.tasks_message_id,
                "archive_message_id": settings.archive_message_id,
            }
            for uid, settings in self._settings.items()
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f)
    
    def set_delay(self, user_id: int, delay_seconds: int):
        """Установить задержку для конкретного пользователя"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].delay = delay_seconds
        self._save()
    
    def get_user_delay(self, user_id: int) -> int:
        """Получить задержку пользователя или дефолтную"""
        from bot.config import settings
        return self._settings.get(user_id, settings.DEFAULT_SUMMARIZE_DELAY).delay
    
    def get_counters(self, user_id: int) -> UserSettingsModel:
        """Получить счетчики ID для пользователя"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        return self._settings[user_id]
    
    def update_last_task_id(self, user_id: int, new_id: int):
        """Обновить последний использованный ID задачи"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].last_task_id = new_id
        self._save()
    
    def update_last_note_id(self, user_id: int, new_id: int):
        """Обновить последний использованный ID заметки"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].last_note_id = new_id
        self._save()
    
    def update_last_message_id(self, user_id: int, new_id: int):
        """Обновить последний использованный ID сообщения"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].last_message_id = new_id
        self._save()
    
    def update_tasks_message_id(self, user_id: int, new_id: int):
        """Обновить ID последнего сообщения /tasks"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].tasks_message_id = new_id
        self._save()
    
    def update_archive_message_id(self, user_id: int, new_id: int):
        """Обновить ID последнего сообщения /archive"""
        if user_id not in self._settings:
            self._settings[user_id] = UserSettingsModel(delay=300)
        self._settings[user_id].archive_message_id = new_id
        self._save()


user_settings = UserSettings()