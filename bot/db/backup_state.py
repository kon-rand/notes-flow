"""
Модуль для хранения состояния бэкапов пользователей.

Хранит информацию о последнем бэкапе для каждого пользователя:
- timestamp: время последнего бэкапа
- hash: хэш (или контрольная сумма) содержимого бэкапа
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BackupState:
    """Состояние бэкапа для одного пользователя."""
    
    def __init__(
        self,
        user_id: int,
        last_backup_timestamp: Optional[datetime] = None,
        last_backup_hash: Optional[str] = None
    ):
        self.user_id = user_id
        self.last_backup_timestamp = last_backup_timestamp
        self.last_backup_hash = last_backup_hash
    
    def to_dict(self) -> dict:
        """Конвертировать в словарь для сохранения в JSON."""
        return {
            'user_id': self.user_id,
            'last_backup_timestamp': self.last_backup_timestamp.isoformat() if self.last_backup_timestamp else None,
            'last_backup_hash': self.last_backup_hash,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BackupState':
        """Создать из словаря из JSON."""
        timestamp = None
        if data.get('last_backup_timestamp'):
            try:
                timestamp = datetime.fromisoformat(data['last_backup_timestamp'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid timestamp for user {data.get('user_id')}: {data.get('last_backup_timestamp')}")
        
        return cls(
            user_id=data['user_id'],
            last_backup_timestamp=timestamp,
            last_backup_hash=data.get('last_backup_hash')
        )
    
    def __repr__(self) -> str:
        return f"BackupState(user_id={self.user_id}, timestamp={self.last_backup_timestamp}, hash={self.last_backup_hash})"


class BackupStateManager:
    """Управление состоянием бэкапов для всех пользователей."""
    
    def __init__(self, state_file: str = "data/backup_state.json"):
        self.state_file = Path(state_file)
        self._ensure_state_file()
    
    def _ensure_state_file(self) -> None:
        """Создать файл состояния если его нет."""
        if not self.state_file.parent.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._save_state({})
    
    def _load_state(self) -> dict:
        """Загрузить состояние из файла."""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load backup state: {e}")
            return {}
    
    def _save_state(self, state: dict) -> None:
        """Сохранить состояние в файл."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save backup state: {e}")
            raise
    
    def get_last_state(self, user_id: int) -> Optional[BackupState]:
        """
        Получить последнее состояние бэкапа для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            BackupState если состояние найдено, иначе None
        """
        state = self._load_state()
        user_state = state.get(str(user_id))
        
        if user_state:
            return BackupState.from_dict(user_state)
        return None
    
    def save_state(
        self,
        user_id: int,
        timestamp: datetime,
        hash: str
    ) -> None:
        """
        Сохранить состояние бэкапа для пользователя.
        
        Args:
            user_id: ID пользователя
            timestamp: Время создания бэкапа
            hash: Хэш содержимого бэкапа
        """
        state = self._load_state()
        
        backup_state = BackupState(
            user_id=user_id,
            last_backup_timestamp=timestamp,
            last_backup_hash=hash
        )
        
        state[str(user_id)] = backup_state.to_dict()
        self._save_state(state)
        
        logger.info(
            f"Backup state saved for user {user_id}: "
            f"timestamp={timestamp.isoformat()}, hash={hash}"
        )
    
    def get_all_user_ids(self) -> list[int]:
        """Получить список всех пользователей с состоянием бэкапа."""
        state = self._load_state()
        return [int(user_id) for user_id in state.keys()]
    
    def delete_state(self, user_id: int) -> None:
        """Удалить состояние пользователя (например, при удалении аккаунта)."""
        state = self._load_state()
        if str(user_id) in state:
            del state[str(user_id)]
            self._save_state(state)
            logger.info(f"Backup state deleted for user {user_id}")
